"""LLM provider boundary. Every LLM call goes through here (AGENTS.md).

SATYA_LLM=mock (the default) runs with no network and no keys. SATYA_LLM=live builds a Sarvam-primary,
Claude-failover chain from whichever keys are present in the environment (P8). Keys are read from env only and
never logged or put into error messages.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(Protocol):
    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse: ...


class ProviderError(Exception):
    """A provider call failed (network, HTTP error, bad payload). Triggers failover."""


class ProviderConfigError(RuntimeError):
    """Live mode requested but no usable key/config is present."""


@dataclass
class Attempt:
    provider: str
    model: str
    outcome: str  # ok | error
    latency_ms: int
    response: LLMResponse | None = None
    error: str | None = None


class AllProvidersFailed(ProviderError):
    def __init__(self, attempts: list[Attempt]):
        self.attempts = attempts
        super().__init__("all providers failed: " + "; ".join(f"{a.provider}: {a.error}" for a in attempts))


class MockProvider:
    """Deterministic offline provider: same prompt in, same text out. Task prompts (see engine.prompts) get
    deterministic JSON so extraction/generation/verification run end to end with no network."""

    name = "mock"
    model = "mock-1"

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        from engine.prompts.mock_responses import mock_task_response

        text = mock_task_response(prompt)
        if text is None:
            text = f"[mock:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:12]}]"
        return LLMResponse(
            text=text,
            provider=self.name,
            model=self.model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=max(1, len(text.split())),
        )


Transport = Callable[[str, dict[str, str], dict, float], dict]


def _urllib_transport(url: str, headers: dict[str, str], body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers={"content-type": "application/json", **headers}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (fixed https endpoints)
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ProviderError(f"HTTP {e.code}") from None  # no body/headers: they may echo secrets
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ProviderError(type(e).__name__) from None


class _HTTPProvider:
    name = ""
    env_key = ""
    default_model = ""
    env_model = ""

    def __init__(self, api_key: str | None = None, model: str | None = None, transport: Transport | None = None,
                 timeout: float = 30.0):  # fmt: skip
        self._key = api_key if api_key is not None else os.environ.get(self.env_key, "")
        if not self._key:
            raise ProviderConfigError(f"{self.env_key} is not set")
        self.model = model or os.environ.get(self.env_model, "") or self.default_model
        self._transport = transport or _urllib_transport
        self._timeout = timeout

    def __repr__(self) -> str:  # never show the key
        return f"{type(self).__name__}(model={self.model!r})"


class SarvamProvider(_HTTPProvider):
    name = "sarvam"
    env_key = "SARVAM_API_KEY"
    env_model = "SARVAM_MODEL"
    default_model = "sarvam-105b"  # override with SARVAM_MODEL if the served id differs
    url = "https://api.sarvam.ai/v1/chat/completions"

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"model": self.model, "messages": messages, "temperature": 0.2}
        data = self._transport(self.url, {"api-subscription-key": self._key}, body, self._timeout)
        try:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            return LLMResponse(text, self.name, self.model, int(usage.get("prompt_tokens", 0)),
                               int(usage.get("completion_tokens", 0)))  # fmt: skip
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError("malformed Sarvam response") from None


class ClaudeProvider(_HTTPProvider):
    name = "claude"
    env_key = "ANTHROPIC_API_KEY"
    env_model = "ANTHROPIC_MODEL"
    default_model = "claude-sonnet-5-5"
    url = "https://api.anthropic.com/v1/messages"

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        body: dict = {"model": self.model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        data = self._transport(
            self.url, {"x-api-key": self._key, "anthropic-version": "2023-06-01"}, body, self._timeout
        )
        try:
            text = "".join(b["text"] for b in data["content"] if b.get("type") == "text")
            usage = data.get("usage") or {}
            return LLMResponse(text, self.name, self.model, int(usage.get("input_tokens", 0)),
                               int(usage.get("output_tokens", 0)))  # fmt: skip
        except (KeyError, TypeError, ValueError):
            raise ProviderError("malformed Claude response") from None


@dataclass
class FailoverProvider:
    """Try providers in order; the first success wins. Every attempt is returned so telemetry can log it (P26)."""

    providers: list = field(default_factory=list)

    def complete_attempts(self, prompt: str, *, system: str | None = None) -> tuple[LLMResponse, list[Attempt]]:
        attempts: list[Attempt] = []
        for p in self.providers:
            t0 = time.perf_counter()
            try:
                resp = p.complete(prompt, system=system)
            except ProviderError as e:
                attempts.append(Attempt(p.name, p.model, "error", _ms(t0), error=str(e)))
                continue
            attempts.append(Attempt(p.name, p.model, "ok", _ms(t0), response=resp))
            return resp, attempts
        raise AllProvidersFailed(attempts)

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        return self.complete_attempts(prompt, system=system)[0]


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def llm_mode() -> str:
    return os.environ.get("SATYA_LLM", "mock").strip().lower() or "mock"


def get_provider() -> LLMProvider:
    mode = llm_mode()
    if mode == "mock":
        return MockProvider()
    if mode == "live":
        chain = [cls() for cls in (SarvamProvider, ClaudeProvider) if os.environ.get(cls.env_key)]
        if not chain:
            raise ProviderConfigError("SATYA_LLM=live but neither SARVAM_API_KEY nor ANTHROPIC_API_KEY is set")
        return FailoverProvider(chain)
    raise ValueError(f"SATYA_LLM={mode!r}: expected 'mock' or 'live'")

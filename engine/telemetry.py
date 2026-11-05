"""llm_calls telemetry: provider, model, tokens, INR cost, latency, prompt version, outcome (P26). Owner: Engine.

Every engine LLM call goes through `call_llm`, which records one `LLMCall` per provider attempt. Platform plugs a
Supabase writer in with `recorder.add_sink(fn)`; by default records are kept in memory only.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from engine.providers import AllProvidersFailed, Attempt, LLMProvider, LLMResponse, ProviderError

# INR per 1M tokens (input, output). ESTIMATES: verify against current provider price sheets and override
# with SATYA_USD_INR / edit here. Mock is free.
USD_INR = float(os.environ.get("SATYA_USD_INR", "85"))
PRICE_INR_PER_MTOK: dict[str, tuple[float, float]] = {
    "mock": (0.0, 0.0),
    "sarvam": (50.0, 150.0),
    "claude": (3.0 * USD_INR, 15.0 * USD_INR),
}


def cost_inr(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = PRICE_INR_PER_MTOK.get(provider, (0.0, 0.0))
    return round((prompt_tokens * pin + completion_tokens * pout) / 1_000_000, 6)


class LLMCall(BaseModel):
    """Row shape for the `llm_calls` table."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    purpose: str  # extract | generate | verify
    prompt_version: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_inr: float = 0.0
    latency_ms: int = 0
    outcome: str  # ok | error
    error: str | None = None
    failover_from: str | None = None  # provider that failed just before this attempt


class CallRecorder:
    def __init__(self) -> None:
        self.calls: list[LLMCall] = []
        self._sinks: list[Callable[[LLMCall], None]] = []

    def add_sink(self, fn: Callable[[LLMCall], None]) -> None:
        self._sinks.append(fn)

    def record(self, call: LLMCall) -> None:
        self.calls.append(call)
        for s in self._sinks:
            s(call)

    def total_cost_inr(self) -> float:
        return round(sum(c.cost_inr for c in self.calls), 6)

    def clear(self) -> None:
        self.calls.clear()


recorder = CallRecorder()


def _record_attempts(attempts: list[Attempt], purpose: str, prompt_version: str, rec: CallRecorder) -> None:
    prev: str | None = None
    for a in attempts:
        r = a.response
        pt, ct = (r.prompt_tokens, r.completion_tokens) if r else (0, 0)
        rec.record(LLMCall(
            purpose=purpose, prompt_version=prompt_version, provider=a.provider, model=a.model,
            prompt_tokens=pt, completion_tokens=ct, cost_inr=cost_inr(a.provider, pt, ct),
            latency_ms=a.latency_ms, outcome=a.outcome, error=a.error, failover_from=prev,
        ))  # fmt: skip
        prev = a.provider if a.outcome == "error" else None


def call_llm(
    provider: LLMProvider,
    prompt: str,
    *,
    system: str | None = None,
    purpose: str,
    prompt_version: str,
    rec: CallRecorder | None = None,
) -> LLMResponse:
    """Call the provider (with failover if it supports it) and record every attempt."""
    rec = rec or recorder
    if hasattr(provider, "complete_attempts"):
        try:
            resp, attempts = provider.complete_attempts(prompt, system=system)
        except AllProvidersFailed as e:
            _record_attempts(e.attempts, purpose, prompt_version, rec)
            raise
        _record_attempts(attempts, purpose, prompt_version, rec)
        return resp
    t0 = time.perf_counter()
    name, model = getattr(provider, "name", "unknown"), getattr(provider, "model", "unknown")
    try:
        resp = provider.complete(prompt, system=system)
    except ProviderError as e:
        _record_attempts([Attempt(name, model, "error", int((time.perf_counter() - t0) * 1000), error=str(e))],
                         purpose, prompt_version, rec)  # fmt: skip
        raise
    _record_attempts([Attempt(resp.provider, resp.model, "ok", int((time.perf_counter() - t0) * 1000), resp)],
                     purpose, prompt_version, rec)  # fmt: skip
    return resp

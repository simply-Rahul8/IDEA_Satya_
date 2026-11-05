"""Machine-translation providers: IndicTrans2 on Cloudflare first, Sarvam Translate as fallback (P8, P13).

These are MT endpoints, not chat LLMs, but they follow the same rules as engine.providers: SATYA_LLM=mock runs offline
with no keys, keys come from the environment only and never appear in errors or reprs.
"""

from __future__ import annotations

import os
from typing import Protocol

from engine.providers import ProviderConfigError, ProviderError, Transport, _urllib_transport, llm_mode


class Translator(Protocol):
    name: str

    def translate(self, text: str, *, source: str = "en", target: str = "hi") -> str: ...


class MockTranslator:
    """Deterministic offline stand-in: marks the text as Hindi and passes everything else (placeholders included)
    through untouched. It is not a translation; it exists so the pipeline runs with no network."""

    name = "mock"

    def translate(self, text: str, *, source: str = "en", target: str = "hi") -> str:
        return f"हिंदी: {text}"


class IndicTrans2Translator:
    """IndicTrans2 served from a Cloudflare Worker (INDICTRANS2_URL, bearer INDICTRANS2_TOKEN). The Worker contract is
    assumed, not verified: POST {text, source_lang, target_lang} -> {translation}. Confirm with whoever deploys it."""

    name = "indictrans2"

    def __init__(self, url: str | None = None, token: str | None = None, transport: Transport | None = None,
                 timeout: float = 30.0):  # fmt: skip
        self._url = url if url is not None else os.environ.get("INDICTRANS2_URL", "")
        self._token = token if token is not None else os.environ.get("INDICTRANS2_TOKEN", "")
        if not self._url:
            raise ProviderConfigError("INDICTRANS2_URL is not set")
        self._transport = transport or _urllib_transport
        self._timeout = timeout

    def translate(self, text: str, *, source: str = "en", target: str = "hi") -> str:
        headers = {"authorization": f"Bearer {self._token}"} if self._token else {}
        body = {"text": text, "source_lang": source, "target_lang": target}
        data = self._transport(self._url, headers, body, self._timeout)
        out = data.get("translation") if isinstance(data, dict) else None
        if not isinstance(out, str) or not out.strip():
            raise ProviderError("malformed IndicTrans2 response")
        return out

    def __repr__(self) -> str:  # never show the URL or token
        return "IndicTrans2Translator()"


class SarvamTranslator:
    """Sarvam Translate (api.sarvam.ai/translate). Request and response shape written from memory of Sarvam's public
    docs and not checked against a live call."""

    name = "sarvam-translate"
    url = "https://api.sarvam.ai/translate"
    model = "sarvam-translate:v1"

    def __init__(self, api_key: str | None = None, transport: Transport | None = None, timeout: float = 30.0):
        self._key = api_key if api_key is not None else os.environ.get("SARVAM_API_KEY", "")
        if not self._key:
            raise ProviderConfigError("SARVAM_API_KEY is not set")
        self._transport = transport or _urllib_transport
        self._timeout = timeout

    def translate(self, text: str, *, source: str = "en", target: str = "hi") -> str:
        body = {
            "input": text,
            "source_language_code": f"{source}-IN",
            "target_language_code": f"{target}-IN",
            "model": self.model,
            "mode": "formal",
        }
        data = self._transport(self.url, {"api-subscription-key": self._key}, body, self._timeout)
        out = data.get("translated_text") if isinstance(data, dict) else None
        if not isinstance(out, str) or not out.strip():
            raise ProviderError("malformed Sarvam Translate response")
        return out

    def __repr__(self) -> str:
        return "SarvamTranslator()"


def get_translators() -> list[Translator]:
    """Primary then fallback. Mock mode (the default) returns only the offline mock."""
    mode = llm_mode()
    if mode == "mock":
        return [MockTranslator()]
    if mode == "live":
        chain: list[Translator] = []
        if os.environ.get("INDICTRANS2_URL"):
            chain.append(IndicTrans2Translator())
        if os.environ.get("SARVAM_API_KEY"):
            chain.append(SarvamTranslator())
        if not chain:
            raise ProviderConfigError("SATYA_LLM=live but neither INDICTRANS2_URL nor SARVAM_API_KEY is set")
        return chain
    raise ValueError(f"SATYA_LLM={mode!r}: expected 'mock' or 'live'")

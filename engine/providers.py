"""LLM provider boundary. Every LLM call goes through here (AGENTS.md).

SATYA_LLM=mock (the default) runs with no network and no keys. Real providers
(Sarvam, Claude failover) are added by the Engine agent behind the same interface.
"""

import hashlib
import os
from dataclasses import dataclass
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


class MockProvider:
    """Deterministic offline provider: same prompt in, same text out."""

    name = "mock"
    model = "mock-1"

    def complete(self, prompt: str, *, system: str | None = None) -> LLMResponse:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        return LLMResponse(
            text=f"[mock:{digest}]",
            provider=self.name,
            model=self.model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=1,
        )


def llm_mode() -> str:
    return os.environ.get("SATYA_LLM", "mock").strip().lower() or "mock"


def get_provider() -> LLMProvider:
    mode = llm_mode()
    if mode == "mock":
        return MockProvider()
    raise NotImplementedError(f"SATYA_LLM={mode!r}: live providers not implemented yet (Engine agent)")

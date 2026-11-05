"""Deterministic offline answers for the task prompts, so SATYA_LLM=mock runs the whole pipeline."""

from __future__ import annotations

import json
import re

from engine.prompts import read_payload

_BULLETS = 5


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]


def _extract(d: dict) -> dict:
    lines = [ln.strip() for ln in d["listing_text"].splitlines() if ln.strip()]
    name = lines[0][:120] if lines else "Unnamed product"
    rest = _sentences("\n".join(lines[1:]))
    return {"product_name": name, "claims": [{"text": s} for s in rest]}


def _s(text: str, typ: str, *anchors: str) -> dict:
    return {"text": text, "type": typ, "anchors": list(anchors)}


def _generate(d: dict) -> dict:
    t = d["product_truth"]
    claims = [c for c in t.get("claims", []) if c.get("status") == "confirmed"]
    name = t["product_name"]
    facts = [_s(f"{name} comes in {t['size']}.", "product_fact", "truth:size")] if t.get("size") else []
    if t.get("ingredients"):
        facts.append(_s("Ingredients: " + ", ".join(t["ingredients"]) + ".", "product_fact", "truth:ingredients"))
    bullets = [_s(c["text"], "benefit_claim", f"claim:{c['id']}") for c in claims] + facts
    bullets = (bullets + [_s(name + ".", "product_fact", "truth:product_name")] * _BULLETS)[:_BULLETS]
    secs = {"title": [_s(name, "product_fact", "truth:product_name")]}
    for i, b in enumerate(bullets, 1):
        secs[f"bullet_{i}"] = [b]
    secs["description"] = [_s(name + ".", "product_fact", "truth:product_name")] + [
        _s(c["text"], "benefit_claim", f"claim:{c['id']}") for c in claims
    ]
    secs["how_to_use"] = [_s(t["how_to_use"], "usage", "truth:how_to_use")] if t.get("how_to_use") else []
    ws = [_s(t[k], ty, f"truth:{k}") for k, ty in (("warnings", "warning"), ("storage", "storage")) if t.get(k)]
    secs["warnings_storage"] = ws
    secs["seo_title"] = [_s(name, "product_fact", "truth:product_name")]
    secs["seo_description"] = [_s(name + ".", "product_fact", "truth:product_name")]
    return {"sections": [{"key": k, "sentences": v} for k, v in secs.items()]}


def _verify(d: dict) -> dict:
    return {"verdicts": [{"index": s["index"], "supported": "UNSUPPORTED-MOCK" not in s["text"], "reason": "mock"}
                         for s in d["sentences"]]}  # fmt: skip


_TASKS = {"extract_product_truth": _extract, "generate_pack": _generate, "verify_pack": _verify}


def mock_task_response(prompt: str) -> str | None:
    parsed = read_payload(prompt)
    if not parsed or parsed[0] not in _TASKS:
        return None
    return json.dumps(_TASKS[parsed[0]](parsed[1]), ensure_ascii=False)

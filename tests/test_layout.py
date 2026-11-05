"""Guards the plan section 5 layout so owners don't have to rediscover it."""

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE_PACKAGES = [
    "models", "rules", "normalize", "guardrails", "verifier",
    "extract", "prompts", "translate", "pipeline", "export", "jobs",
]  # fmt: skip
ENGINE_MODULES = ["providers", "telemetry", "product_type"]
DIRS = ["web/components", "api", "supabase", "data/corpus", "data/samples", "bench"]


@pytest.mark.parametrize("name", [*ENGINE_PACKAGES, *ENGINE_MODULES])
def test_engine_importable(name):
    importlib.import_module(f"engine.{name}")


@pytest.mark.parametrize("path", DIRS)
def test_dirs_exist(path):
    assert (ROOT / path).is_dir()


def test_env_example_defaults_to_mock():
    assert "SATYA_LLM=mock" in (ROOT / ".env.example").read_text()

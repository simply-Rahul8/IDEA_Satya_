import os

# Tests never touch the network or real keys.
os.environ["SATYA_LLM"] = "mock"

import pytest  # noqa: E402

from engine.repo import MemoryRepository  # noqa: E402
from web import packs  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_repository():
    """Every test starts with an empty in-memory repository: no pack exists until a test puts one there."""
    packs.reset(MemoryRepository())
    yield
    packs.reset(None)

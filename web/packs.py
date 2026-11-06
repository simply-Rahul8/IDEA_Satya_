"""The process's pack repository and the dev-only seed. Routes get packs only through `repo()` and a workspace."""

from __future__ import annotations

import os
import threading

from fastapi import Request

from engine.repo import MemoryRepository, PackRepository, from_env
from engine.repo import evidence as evidence_store
from web.security import workspace_of

__all__ = ["dev_seed", "evidence", "repo", "reset", "workspace_of"]

_repo: PackRepository | None = None
_evidence: evidence_store.EvidenceStore | None = None
_lock = threading.Lock()


def repo() -> PackRepository:
    """Supabase when configured, otherwise in memory (local/dev/test only; hosted environments fail closed)."""
    global _repo
    with _lock:
        if _repo is None:
            _repo = from_env()
        return _repo


def evidence() -> evidence_store.EvidenceStore:
    """The private evidence bucket (Supabase Storage), or memory in local/dev/test."""
    global _evidence
    with _lock:
        if _evidence is None:
            _evidence = evidence_store.from_env()
        return _evidence


def reset(new: PackRepository | None = None) -> None:
    """Swap or clear the repository and the evidence store (tests)."""
    global _repo, _evidence
    with _lock:
        _repo = new
        _evidence = None


def dev_seed(request: Request) -> None:
    """Router dependency. Only with SATYA_ENV=dev and an in-memory repository, and only once per workspace."""
    if os.environ.get("SATYA_ENV") != "dev":
        return
    store = repo()
    if not isinstance(store, MemoryRepository):
        return
    from web import devseed

    ws = workspace_of(request)
    if not store.exists(ws, devseed.PACK_ID):
        devseed.seed(store, ws)

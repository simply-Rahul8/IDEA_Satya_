"""Workspace-scoped pack repository (plan section 5, ADR-8, ADR-12 item 2). Owner: Platform.

Every call takes the workspace id first and can only reach that workspace's packs: an id that belongs to
another workspace is indistinguishable from one that does not exist (`NotFound`, a 404 at the web layer).
Two implementations share the interface: `MemoryRepository` (tests, local dev) and `SupabaseRepository`
(env config; see docs/deploy.md). Nothing here is process-global except what the caller chooses to share.
"""

from __future__ import annotations

import os
import re
import threading
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from engine.repo.rest import PostgrestClient, Rest
from engine.repo.state import Keep, ReviewState, from_row, to_row

__all__ = [
    "Conflict",
    "Keep",
    "MemoryRepository",
    "NotFound",
    "PackRepository",
    "ReviewState",
    "SupabaseRepository",
    "from_env",
]

_UUID = re.compile(r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$", re.I)


class NotFound(LookupError):
    """No such pack in this workspace (whether or not it exists in another one)."""


class Conflict(RuntimeError):
    """The pack changed while it was being edited."""


class PackRepository(Protocol):
    def get(self, workspace_id: str, pack_id: str) -> ReviewState: ...

    def put(self, workspace_id: str, state: ReviewState) -> None:
        """Create the pack, or replace it when it already exists in this workspace."""

    def edit(self, workspace_id: str, pack_id: str):
        """Context manager yielding the state; changes are saved when the block exits without an exception."""

    def exists(self, workspace_id: str, pack_id: str) -> bool: ...


class MemoryRepository:
    """In-process store keyed by (workspace, pack). Workspaces are evicted least-recently-used so an open
    preview cannot grow without bound. Not for hosted use: state would differ per serverless instance."""

    def __init__(self, max_workspaces: int = 500) -> None:
        self._packs: dict[tuple[str, str], ReviewState] = {}
        self._workspaces: OrderedDict[str, None] = OrderedDict()
        self._max = max_workspaces
        self._lock = threading.RLock()

    def put(self, workspace_id: str, state: ReviewState) -> None:
        with self._lock:
            self._workspaces[workspace_id] = None
            self._workspaces.move_to_end(workspace_id)
            while len(self._workspaces) > self._max:
                old, _ = self._workspaces.popitem(last=False)
                for k in [k for k in self._packs if k[0] == old]:
                    del self._packs[k]
            self._packs[(workspace_id, state.pack_id)] = state

    def get(self, workspace_id: str, pack_id: str) -> ReviewState:
        with self._lock:
            try:
                state = self._packs[(workspace_id, pack_id)]
            except KeyError:
                raise NotFound(pack_id) from None
            self._workspaces.move_to_end(workspace_id)
            return state

    def exists(self, workspace_id: str, pack_id: str) -> bool:
        return (workspace_id, pack_id) in self._packs

    @contextmanager
    def edit(self, workspace_id: str, pack_id: str) -> Iterator[ReviewState]:
        with self._lock:  # one writer at a time; the state object is mutated in place
            yield self.get(workspace_id, pack_id)


class SupabaseRepository:
    """`packs` rows in Supabase Postgres through PostgREST with the service-role key (never the browser's).

    The service role bypasses RLS, so scoping is enforced here: every query filters on `workspace_id`, and the
    schema's composite foreign keys keep child rows in the same workspace. Edits use a revision counter, so two
    overlapping saves cannot silently overwrite each other (`Conflict`).
    """

    TABLE = "packs"

    def __init__(self, rest: Rest) -> None:
        self._rest = rest

    @staticmethod
    def _valid(value: str) -> bool:
        return bool(_UUID.match(value))

    def _row(self, workspace_id: str, pack_id: str) -> dict[str, Any]:
        if not self._valid(pack_id) or not self._valid(workspace_id):
            raise NotFound(pack_id)
        rows = self._rest.select(self.TABLE, {"id": pack_id, "workspace_id": workspace_id})
        if not rows:
            raise NotFound(pack_id)
        return rows[0]

    def get(self, workspace_id: str, pack_id: str) -> ReviewState:
        return from_row(pack_id, self._row(workspace_id, pack_id))

    def exists(self, workspace_id: str, pack_id: str) -> bool:
        try:
            self._row(workspace_id, pack_id)
        except NotFound:
            return False
        return True

    def put(self, workspace_id: str, state: ReviewState) -> None:
        if not self._valid(state.pack_id) or not self._valid(workspace_id):
            raise ValueError("pack and workspace ids must be UUIDs")
        values = to_row(state)
        rows = self._rest.update(self.TABLE, {"id": state.pack_id, "workspace_id": workspace_id}, values)
        if not rows:
            self._rest.insert(self.TABLE, {"id": state.pack_id, "workspace_id": workspace_id, "rev": 0, **values})

    @contextmanager
    def edit(self, workspace_id: str, pack_id: str) -> Iterator[ReviewState]:
        row = self._row(workspace_id, pack_id)
        state = from_row(pack_id, row)
        yield state
        saved = self._rest.update(
            self.TABLE,
            {"id": pack_id, "workspace_id": workspace_id, "rev": row["rev"]},
            {**to_row(state), "rev": row["rev"] + 1},
        )
        if not saved:
            raise Conflict(pack_id)


def from_env(env: dict[str, str] | None = None) -> PackRepository:
    """Supabase when SUPABASE_URL and the service-role key are set; in-memory only for local/dev/test.

    Hosted environments (preview/production, or Vercel) fail closed without Supabase: an in-process store
    there would be per-instance and lost on every cold start.
    """
    env = os.environ if env is None else env
    url, key = env.get("SUPABASE_URL", ""), env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and key:
        return SupabaseRepository(PostgrestClient(url, key))
    if env.get("SATYA_ENV", "local") in ("preview", "production") or env.get("VERCEL"):
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required when SATYA_ENV is preview/production"
        )
    return MemoryRepository()

"""A fake PostgREST client for the Supabase repository: same filtering and write semantics, in memory."""

import copy
import json
from typing import Any


class FakeRest:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.calls: list[tuple[str, str, dict]] = []

    def _match(self, row: dict, eq: dict) -> bool:
        return all(str(row.get(k)) == str(v) for k, v in eq.items())

    def select(self, table, eq):
        self.calls.append(("select", table, dict(eq)))
        return [copy.deepcopy(r) for r in self.tables.get(table, []) if self._match(r, eq)]

    def insert(self, table, row):
        self.calls.append(("insert", table, dict(row)))
        rows = self.tables.setdefault(table, [])
        if any(r["id"] == row["id"] for r in rows):
            raise RuntimeError("duplicate key")  # primary key is global, as in Postgres
        stored = json.loads(json.dumps(row))  # what comes back has been through JSON, like the wire
        rows.append(stored)
        return copy.deepcopy(stored)

    def update(self, table, eq, values):
        self.calls.append(("update", table, dict(eq)))
        out = []
        for r in self.tables.get(table, []):
            if self._match(r, eq):
                r.update(json.loads(json.dumps(values)))
                out.append(copy.deepcopy(r))
        return out

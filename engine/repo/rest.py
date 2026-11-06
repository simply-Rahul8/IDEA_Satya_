"""The small PostgREST surface the repository needs, and an HTTP implementation using only the stdlib."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol


class Rest(Protocol):
    def select(self, table: str, eq: dict[str, Any]) -> list[dict[str, Any]]: ...

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]: ...

    def update(self, table: str, eq: dict[str, Any], values: dict[str, Any]) -> list[dict[str, Any]]:
        """Rows that matched `eq` and were updated (empty when none matched)."""


class PostgrestClient:
    def __init__(self, url: str, service_key: str, timeout: float = 10.0) -> None:
        self._base = url.rstrip("/") + "/rest/v1/"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }
        self._timeout = timeout

    def _call(self, method: str, table: str, eq: dict[str, Any], body: Any = None, prefer: str = "") -> list[dict]:
        query = urllib.parse.urlencode({k: f"eq.{v}" for k, v in eq.items()})
        req = urllib.request.Request(
            f"{self._base}{urllib.parse.quote(table)}" + (f"?{query}" if query else ""),
            data=None if body is None else json.dumps(body).encode(),
            method=method,
            headers={**self._headers, **({"Prefer": prefer} if prefer else {})},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 (URL is env config)
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Supabase {method} {table} failed: HTTP {e.code}") from None  # body may hold data
        return json.loads(raw) if raw else []

    def select(self, table: str, eq: dict[str, Any]) -> list[dict[str, Any]]:
        return self._call("GET", table, eq)

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        return self._call("POST", table, {}, row, "return=representation")[0]

    def update(self, table: str, eq: dict[str, Any], values: dict[str, Any]) -> list[dict[str, Any]]:
        return self._call("PATCH", table, eq, values, "return=representation")


class MemoryRest:
    """Dict-backed `Rest` for local dev with no Supabase configured (not for hosted use)."""

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}

    def select(self, table: str, eq: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(r) for r in self.tables.get(table, []) if all(str(r.get(k)) == str(v) for k, v in eq.items())]

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        self.tables.setdefault(table, []).append(dict(row))
        return dict(row)

    def update(self, table: str, eq: dict[str, Any], values: dict[str, Any]) -> list[dict[str, Any]]:
        hit = [r for r in self.tables.get(table, []) if all(str(r.get(k)) == str(v) for k, v in eq.items())]
        for r in hit:
            r.update(values)
        return [dict(r) for r in hit]

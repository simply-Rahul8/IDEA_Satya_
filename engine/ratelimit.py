"""Rate limits (P9). Owner: Platform.

`hit()` is a thin wrapper over rate_limit_hit() in schema.sql. The web layer uses the limiter classes:
`SharedLimiter` counts in Postgres (one count across every serverless instance), `MemoryLimiter` is the
per-process fallback for local dev and for when the database is unreachable.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


def hit(conn, key: str, limit: int, window_seconds: int) -> bool:
    """True while `key` is within `limit` hits per window. Call with the service-role connection."""
    with conn.cursor() as cur:
        cur.execute("select rate_limit_hit(%s, %s, %s)", (key, limit, window_seconds))
        allowed = cur.fetchone()[0]
    conn.commit()
    return bool(allowed)


def ip_key(ip: str, scope: str = "") -> str:
    """Public checker is keyed by a hash so raw IPs are not stored (DPDP)."""
    return "ip:" + (scope + ":" if scope else "") + hashlib.sha256(ip.encode()).hexdigest()[:32]


class MemoryLimiter:
    """In-process sliding window. Only correct for a single process."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window_s = limit, window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """None while allowed; otherwise the seconds until the oldest hit leaves the window."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window_s:
                q.popleft()
            if len(q) >= self.limit:
                return max(1, int(self.window_s - (now - q[0])) + 1)
            q.append(now)
            if len(self._hits) > 50_000:  # bound memory under key churn
                self._hits = defaultdict(
                    deque, {k: v for k, v in self._hits.items() if v and now - v[-1] <= self.window_s}
                )
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


class SharedLimiter:
    """Fixed window kept in Postgres via rate_limit_hit(), so the count is shared across instances.

    `connect` returns a service-role psycopg connection. If the database cannot be reached the per-process
    limiter answers instead: a database blip must not turn the limiter off.
    """

    def __init__(self, connect: Callable[[], object], limit: int, window_s: int):
        self.limit, self.window_s = limit, window_s
        self._connect = connect
        self._fallback = MemoryLimiter(limit, window_s)

    def hit(self, key: str) -> int | None:
        try:
            conn = self._connect()
            try:
                allowed = hit(conn, key, self.limit, self.window_s)
            finally:
                close = getattr(conn, "close", None)
                if close:
                    close()
        except Exception:
            return self._fallback.hit(key)
        if allowed:
            return None
        return max(1, self.window_s - int(time.time()) % self.window_s)

    def reset(self) -> None:
        self._fallback.reset()


def make_limiter(limit: int, window_s: int):
    """Postgres-backed when SUPABASE_DB_URL is set, in-process otherwise."""
    dsn = os.environ.get("SUPABASE_DB_URL")
    if not dsn:
        return MemoryLimiter(limit, window_s)

    def connect():
        import psycopg

        return psycopg.connect(dsn, connect_timeout=3)

    return SharedLimiter(connect, limit, window_s)

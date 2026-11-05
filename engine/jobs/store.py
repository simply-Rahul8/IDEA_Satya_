"""Stepwise, client-driven bulk jobs (P11). Owner: Platform.

The browser calls a step endpoint repeatedly; each call claims a few pending items, processes them and
records results, then returns progress. No worker or cron is involved, so a closed tab or a timed-out
function only delays the job: stale claims become claimable again (see claim_job_items in schema.sql).

`conn` is a psycopg connection to the Supabase Postgres, opened with the service-role credentials.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any]], dict[str, Any]]


def create_job(
    conn, workspace_id: str, kind: str, payloads: list[dict[str, Any]], created_by: str | None = None
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "insert into jobs (workspace_id, created_by, kind, total) values (%s, %s, %s, %s) returning id",
            (workspace_id, created_by, kind, len(payloads)),
        )
        job_id = str(cur.fetchone()[0])
        cur.executemany(
            "insert into job_items (job_id, workspace_id, position, payload) values (%s, %s, %s, %s::jsonb)",
            [(job_id, workspace_id, i, json.dumps(p)) for i, p in enumerate(payloads)],
        )
    conn.commit()
    return job_id


def step_job(conn, job_id: str, handler: Handler, batch_size: int = 3, stale_seconds: int = 120) -> dict[str, Any]:
    """Process up to batch_size items. Returns progress: {status, total, done, failed}."""
    with conn.cursor() as cur:
        cur.execute(
            "select * from claim_job_items(%s, %s, make_interval(secs => %s))", (job_id, batch_size, stale_seconds)
        )
        cols = [c.name for c in cur.description]
        items = [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]
    conn.commit()
    for item in items:
        try:
            result, status, error = handler(item["payload"]), "done", None
        except Exception as exc:  # one bad item must not stop the job; it is retried up to max_attempts
            result, status, error = None, "pending", f"{type(exc).__name__}: {exc}"[:500]
        with conn.cursor() as cur:
            cur.execute(
                "update job_items set status = %s, result = %s::jsonb, error = %s, claimed_at = null where id = %s",
                (status, json.dumps(result) if result is not None else None, error, item["id"]),
            )
        conn.commit()
    return job_progress(conn, job_id)


def job_progress(conn, job_id: str) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("select status, total, done, failed from refresh_job(%s)", (job_id,))
        status, total, done, failed = cur.fetchone()
    conn.commit()
    return {"status": status, "total": total, "done": done, "failed": failed}

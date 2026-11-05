"""Rate limits (P9): a thin wrapper over rate_limit_hit() in schema.sql. Owner: Platform."""

import hashlib


def hit(conn, key: str, limit: int, window_seconds: int) -> bool:
    """True while `key` is within `limit` hits per window. Call with the service-role connection."""
    with conn.cursor() as cur:
        cur.execute("select rate_limit_hit(%s, %s, %s)", (key, limit, window_seconds))
        allowed = cur.fetchone()[0]
    conn.commit()
    return bool(allowed)


def ip_key(ip: str) -> str:
    """Public checker is keyed by a hash so raw IPs are not stored (DPDP)."""
    return "ip:" + hashlib.sha256(ip.encode()).hexdigest()[:32]

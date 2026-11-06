"""SAT-50: under the pinned uvicorn arguments a rotating X-Forwarded-For cannot evade the rate limiter.

Starts a real uvicorn (the same SERVER_ARGS `scripts/run.py dev` uses) and posts to /check from 127.0.0.1, the
address uvicorn trusts by default. Without `--no-proxy-headers` uvicorn rewrites `request.client` from the header
and every post gets a fresh count (QA SAT-44: 130 x 200).
"""

import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run as runner  # noqa: E402


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(args: list[str]):
    port = free_port()
    env = {
        **os.environ,
        "SATYA_LLM": "mock",
        "SATYA_ENV": "local",
        "CHECKER_RATE_LIMIT": "3",
        "CHECKER_RATE_WINDOW_S": "600",
    }
    for name in ("VERCEL", "SATYA_TRUSTED_IP_HEADER", "SUPABASE_DB_URL", "FORWARDED_ALLOW_IPS"):
        env.pop(name, None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "asgi:app", "--port", str(port), "--log-level", "warning", *args],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if httpx.get(base + "/healthz", timeout=1).status_code == 200:
                return proc, base
        except httpx.HTTPError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("uvicorn did not start")


def check_codes(base: str, posts: int) -> list[int]:
    with httpx.Client(base_url=base) as c:
        csrf = re.search(r'name="csrf-token" content="([^"]+)"', c.get("/check").text).group(1)
        return [
            c.post(
                "/check",
                data={"text": "hello"},
                headers={"X-CSRF-Token": csrf, "Origin": base, "X-Forwarded-For": f"10.1.0.{i}", "HX-Request": "true"},
            ).status_code
            for i in range(posts)
        ]


def test_dev_task_pins_no_proxy_headers():
    dev = next(cmd for cmd in runner.TASKS["dev"] if "uvicorn" in cmd)
    assert "--no-proxy-headers" in dev


def test_rotating_xff_cannot_evade_the_limiter_under_pinned_server_args():
    proc, base = serve(runner.SERVER_ARGS)
    try:
        assert check_codes(base, 5) == [200, 200, 200, 429, 429]
    finally:
        proc.kill()


def test_default_uvicorn_trusts_xff_which_is_why_the_args_are_pinned():
    """Documents the hazard; if uvicorn's default ever changes this fails and the pin can be reviewed."""
    proc, base = serve([])
    try:
        assert set(check_codes(base, 5)) == {200}
    finally:
        proc.kill()

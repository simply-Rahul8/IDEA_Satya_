"""Cross-platform task runner (the Windows host has no make). Usage: python scripts/run.py <task>."""

import os
import subprocess
import sys

# The app keys rate limits on `request.client`, or on SATYA_TRUSTED_IP_HEADER when that is set (web/security.py).
# uvicorn's default is to trust X-Forwarded-For from 127.0.0.1 and rewrite `request.client` with it, which lets any
# caller rotate that header past the limiter. Every place the app is served must pass these (docs/deploy.md, SAT-50).
SERVER_ARGS = ["--no-proxy-headers"]

TASKS = {
    "test": [["uv", "run", "pytest"]],
    "lint": [["uv", "run", "ruff", "check", "."], ["uv", "run", "ruff", "format", "--check", "."]],
    "format": [["uv", "run", "ruff", "check", "--fix", "."], ["uv", "run", "ruff", "format", "."]],
    "bench": [["uv", "run", "python", "-m", "bench"]],
    "dev": [["uv", "run", "uvicorn", "asgi:app", "--reload", *SERVER_ARGS]],
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in TASKS:
        print(f"usage: run.py {{{'|'.join(TASKS)}}}", file=sys.stderr)
        return 2
    env = {**os.environ, "SATYA_LLM": os.environ.get("SATYA_LLM", "mock")}
    for cmd in TASKS[argv[1]]:
        code = subprocess.call(cmd, env=env)
        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

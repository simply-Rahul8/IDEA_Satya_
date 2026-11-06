"""Test client that behaves like a browser on the site: same-origin headers, session cookie and CSRF token."""

import re

from fastapi.testclient import TestClient

from asgi import app


def secure(client: TestClient | None = None) -> TestClient:
    c = client or TestClient(app)
    token = re.search(r'name="csrf-token" content="([0-9a-f]+)"', c.get("/check").text).group(1)
    c.headers.update({"Origin": "http://testserver", "X-CSRF-Token": token})
    c.owner = c.cookies["satya_sid"].split(".")[0]
    return c

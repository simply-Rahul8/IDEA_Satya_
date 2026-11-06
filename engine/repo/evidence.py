"""Evidence files for test-report claims (P25): the private `evidence` Storage bucket, one folder per workspace.

An object path is `<workspace_id>/<file name>` (the shape `evidence_file_path_ok` checks in supabase/schema.sql).
`MemoryEvidenceStore` serves local dev and tests; `SupabaseEvidenceStore` uploads over the Storage REST API with the
service-role key, which never reaches the browser. Owner: Platform.
"""

from __future__ import annotations

import os
import re
import secrets
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

MAX_BYTES = 10 * 1024 * 1024  # the bucket's file_size_limit
BUCKET = "evidence"
_SIGNATURES = (
    (b"%PDF-", "application/pdf", "pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
)  # the bucket's allowed_mime_types, recognised by content and not by what the browser claims


class EvidenceError(ValueError):
    """The file cannot be stored; the message is safe to show."""


class EvidenceStore(Protocol):
    def put(self, workspace_id: str, filename: str, data: bytes) -> str:
        """Store the file and return its object path (`<workspace_id>/<name>`)."""

    def exists(self, path: str) -> bool: ...


def sniff(data: bytes) -> tuple[str, str]:
    for magic, mime, ext in _SIGNATURES:
        if data.startswith(magic):
            return mime, ext
    raise EvidenceError("Upload a PDF, PNG or JPEG file.")


def object_path(workspace_id: str, filename: str, ext: str) -> str:
    """A safe, unique object path: letters, digits and dashes from the original name plus a random suffix."""
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    stem = re.sub(r"[^A-Za-z0-9]+", "-", base.rsplit(".", 1)[0]).strip("-")[:60] or "evidence"
    return f"{workspace_id}/{stem}-{secrets.token_hex(4)}.{ext}"


def _checked(data: bytes) -> tuple[str, str]:
    if not data:
        raise EvidenceError("That file is empty.")
    if len(data) > MAX_BYTES:
        raise EvidenceError(f"That file is bigger than the {MAX_BYTES // 1_000_000} MB limit.")
    return sniff(data)


class MemoryEvidenceStore:
    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._lock = threading.Lock()

    def put(self, workspace_id: str, filename: str, data: bytes) -> str:
        _, ext = _checked(data)
        path = object_path(workspace_id, filename, ext)
        with self._lock:
            self._files[path] = data
        return path

    def exists(self, path: str) -> bool:
        return path in self._files


class SupabaseEvidenceStore:
    def __init__(self, url: str, service_key: str, timeout: float = 20.0) -> None:
        self._base = url.rstrip("/") + "/storage/v1/object/"
        self._headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
        self._timeout = timeout

    def _url(self, path: str) -> str:
        return self._base + BUCKET + "/" + urllib.parse.quote(path)

    def put(self, workspace_id: str, filename: str, data: bytes) -> str:
        mime, ext = _checked(data)
        path = object_path(workspace_id, filename, ext)
        req = urllib.request.Request(
            self._url(path), data=data, method="POST", headers={**self._headers, "Content-Type": mime}
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout):  # noqa: S310 (URL is env config)
                pass
        except (urllib.error.URLError, OSError):
            raise EvidenceError("We couldn't store that file. Try again in a moment.") from None
        return path

    def exists(self, path: str) -> bool:
        req = urllib.request.Request(self._url(path), method="HEAD", headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout):  # noqa: S310
                return True
        except (urllib.error.URLError, OSError):
            return False


def from_env(env: dict[str, str] | None = None) -> EvidenceStore:
    """Supabase Storage when configured; in memory only for local/dev/test (hosted environments fail closed)."""
    env = os.environ if env is None else env
    url, key = env.get("SUPABASE_URL", ""), env.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and key:
        return SupabaseEvidenceStore(url, key)
    if env.get("SATYA_ENV", "local") in ("preview", "production") or env.get("VERCEL"):
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required when SATYA_ENV is preview/production"
        )
    return MemoryEvidenceStore()

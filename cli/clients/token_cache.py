"""Persist OAuth tokens, keyed by base_url.

Default location: ~/.alation/token_cache.json
In Cowork/container environments: alongside credentials.local (persistent storage).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from .credentials import find_credentials_file

_CACHE_DIR = Path.home() / ".alation"


def _default_cache_path() -> Path:
    """Determine the token cache file path.

    In claude cowork container environment, persist alongside
    credentials.local so the cache survives across sessions.
    """
    if os.environ.get("CLAUDE_CODE_IS_COWORK"):

        creds_file = find_credentials_file()
        if creds_file is not None:
            return creds_file.parent / "token_cache.json"
    return _CACHE_DIR / "token_cache.json"


@dataclass
class TokenEntry:
    """A single cached OAuth token set."""

    access_token: str
    refresh_token: str
    expires_at: float
    token_type: str = "Bearer"

    def is_expired(self, margin_seconds: int = 60) -> bool:
        return time.time() >= (self.expires_at - margin_seconds)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TokenEntry:
        return cls(
            access_token=d["access_token"],
            refresh_token=d.get("refresh_token", ""),
            expires_at=d["expires_at"],
            token_type=d.get("token_type", "Bearer"),
        )


class TokenCache:
    """Read/write OAuth tokens to ~/.alation/token_cache.json."""

    def __init__(self, cache_file: Path | None = None) -> None:
        self._path = cache_file or _default_cache_path()

    def _read_all(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self._path.parent, 0o700)
        self._path.write_text(json.dumps(data, indent=2) + "\n")
        os.chmod(self._path, 0o600)

    def get(self, base_url: str) -> TokenEntry | None:
        data = self._read_all()
        entry = data.get(base_url)
        if entry is None:
            return None
        return TokenEntry.from_dict(entry)

    def put(self, base_url: str, entry: TokenEntry) -> None:
        data = self._read_all()
        data[base_url] = entry.to_dict()
        self._write_all(data)

    def remove(self, base_url: str) -> None:
        data = self._read_all()
        if base_url in data:
            del data[base_url]
            self._write_all(data)

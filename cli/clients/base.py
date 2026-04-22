"""Unified HTTP client for Alation APIs.

Authenticates via OAuth Bearer token (preferred) or session cookie (fallback).
Localhost connections skip authentication.
"""

from __future__ import annotations

import http.cookiejar
import json
import ssl
import time
import sys
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Self

from .auth import OAuthAuth, SessionAuth
from .credentials import load_credentials


class AuthenticationError(Exception):
    """Raised when authentication fails or is missing."""


class _RedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow 307/308 redirects for POST (stdlib only handles GET/HEAD)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if code in (307, 308):
            return urllib.request.Request(
                newurl,
                data=req.data,
                headers=dict(req.unredirected_hdrs),
                origin_req_host=req.origin_req_host,
                unverifiable=True,
                method=req.get_method(),
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


ERR_AUTH_REQUIRED = (
    "No authentication configured. "
    "Use the setup skill to configure credentials."
)
ERR_OAUTH_LOGIN_REQUIRED = (
    "OAuth credentials found but no cached token. "
    "Run 'python -m cli setup login' to authenticate."
)
ERR_CLIENT_NOT_INIT = "Client not initialized. Use 'with' context manager."


class AlationClient:
    """Unified HTTP client for all Alation APIs.

    Credentials are loaded from credentials.local (services.alation section).
    Constructor parameters override credentials.local values when provided.
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        *,
        ai_path: str | None = None,
        disable_ssl_verification: bool | None = None,
    ) -> None:
        creds = load_credentials("alation")

        self.base_url = (base_url or creds.get("base_url", "http://localhost:8000")).rstrip("/")
        self.username = username or creds.get("username", "")
        self.password = password or creds.get("password", "")
        self.client_id = creds.get("client_id", "")
        self.client_secret = creds.get("client_secret", "")

        if ai_path is None:
            ai_path = "" if self._is_local() else "/ai"
        self.ai_path = "/" + ai_path.strip("/") if ai_path else ""

        if disable_ssl_verification is None:
            cred_val = creds.get("disable_ssl_verification", "")
            disable_ssl_verification = cred_val.lower() in ("1", "true", "yes")
        self.disable_ssl_verification = disable_ssl_verification

        self._opener: urllib.request.OpenerDirector | None = None
        self._bearer_token: str | None = None

    def _is_local(self) -> bool:
        return "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def __enter__(self) -> Self:
        cookie_jar = http.cookiejar.CookieJar()
        handlers: list[urllib.request.BaseHandler] = [
            urllib.request.HTTPCookieProcessor(cookie_jar),
            _RedirectHandler(),
        ]
        ssl_ctx: ssl.SSLContext | None = None
        if self.disable_ssl_verification:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            handlers.append(urllib.request.HTTPSHandler(context=ssl_ctx))
        self._opener = urllib.request.build_opener(*handlers)

        if not self._is_local():
            authenticated = False

            # Try OAuth first if client_id is configured
            if self.client_id:
                oauth = OAuthAuth(
                    self.base_url,
                    self.client_id,
                    self.client_secret,
                    ssl_context=ssl_ctx,
                )
                token = oauth.get_valid_token()
                if token:
                    self._bearer_token = token.access_token
                    authenticated = True

            # Fallback to session auth
            if not authenticated:
                if self.username and self.password:
                    auth = SessionAuth(self.base_url, self.username, self.password)
                    auth.authenticate(self._opener, cookie_jar)
                elif self.client_id:
                    raise AuthenticationError(ERR_OAUTH_LOGIN_REQUIRED)
                else:
                    raise AuthenticationError(ERR_AUTH_REQUIRED)

        return self

    def __exit__(self, *args: object) -> None:
        pass

    def _headers(self) -> dict[str, str]:
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    def _url(self, path: str) -> str:
        if path.startswith("/integration/"):
            return f"{self.base_url}{path}"
        return f"{self.base_url}{self.ai_path}{path}"

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_data: Any = None,
        params: dict | None = None,
        timeout: float = 60,
    ) -> Any:
        """Low-level request. Returns urllib response object."""
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)

        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode()

        req = urllib.request.Request(url, data=body, method=method)
        if json_data is not None:
            req.add_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            req.add_header(key, value)

        try:
            return self._opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AuthenticationError(
                    f"HTTP {e.code} {e.reason}. Token may be expired. "
                    "Run 'python -m cli setup check' to diagnose."
                ) from e
            body = ""
            try:
                body = e.read().decode()[:500]
            except Exception:
                pass
            raise urllib.error.HTTPError(
                e.url, e.code, f"{e.reason}: {body}" if body else e.reason,
                e.headers, None,
            ) from e

    def get(self, path: str, params: dict | None = None) -> Any:
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)
        resp = self._request("GET", self._url(path), headers=self._headers(), params=params)
        body = resp.read().decode()
        return json.loads(body) if body else None

    def post(self, path: str, data: dict | None = None, params: dict | None = None) -> Any:
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)
        resp = self._request("POST", self._url(path), headers=self._headers(), json_data=data, params=params)
        if resp.status == HTTPStatus.NO_CONTENT:
            return None
        body = resp.read().decode()
        return json.loads(body) if body else None

    def put(self, path: str, data: Any = None) -> Any:
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)
        resp = self._request("PUT", self._url(path), headers=self._headers(), json_data=data)
        body = resp.read().decode()
        return json.loads(body) if body else None

    def patch(self, path: str, data: dict | None = None) -> Any:
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)
        resp = self._request("PATCH", self._url(path), headers=self._headers(), json_data=data)
        body = resp.read().decode()
        return json.loads(body) if body else None

    def delete(self, path: str) -> None:
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)
        self._request("DELETE", self._url(path), headers=self._headers())

    def _stream_request(
        self,
        method: str,
        path: str,
        *,
        json_data: Any = None,
        params: dict | None = None,
        timeout: float = 300,
    ) -> Any:
        """Make a request and return the raw response for line-by-line SSE reading."""
        return self._request(
            method,
            self._url(path),
            headers=self._headers(),
            json_data=json_data,
            params=params,
            timeout=timeout,
        )


# --- Utilities ---


def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def print_json(data: Any) -> None:
    print(format_json(data))


def print_error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)


# --- Shared async tool polling ---

_DEFAULT_POLL_ATTEMPTS = 10
_DEFAULT_POLL_INTERVAL = 1.0


def poll_tool_result(
    client: AlationClient,
    chat_id: str,
    *,
    max_attempts: int = _DEFAULT_POLL_ATTEMPTS,
    interval: float = _DEFAULT_POLL_INTERVAL,
    default: Any = None,
) -> Any:
    """Poll chat messages for a tool-return part.

    Used by SearchClient and BiClient for async tool endpoints.
    """
    if default is None:
        default = {}
    for _ in range(max_attempts):
        messages = client.get(f"/api/v1/chats/{chat_id}/messages") or {}
        for msg in messages.get("data", []):
            for part in msg.get("model_message", {}).get("parts", []):
                if part.get("part_kind") == "tool-return":
                    content = part.get("content", "")
                    try:
                        return json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        if content:
                            return {"raw_content": content}
                        return default
        time.sleep(interval)
    return default

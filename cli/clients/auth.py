"""Authentication for Alation APIs.

Supports two auth methods:

1. OAuth (Authorization Code + PKCE) — preferred
   Uses OIDC discovery, browser-based login, and Bearer tokens.

2. Django session login — fallback
   GET /login/ (CSRF token) -> POST /login/ (credentials) -> session cookie.

The session cookie (plus jwt_session) is handled automatically by the
opener's HTTPCookieProcessor. No explicit header management needed.
"""

from __future__ import annotations

import hashlib
import http.cookiejar
import http.server
import json
import secrets
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from base64 import urlsafe_b64encode

from .token_cache import TokenCache, TokenEntry


class SessionAuth:
    """Authenticate via Django session login. Cookies are managed by the opener."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password

    def authenticate(self, opener: urllib.request.OpenerDirector, cookie_jar: http.cookiejar.CookieJar) -> None:
        """GET /login/ for CSRF token, then POST credentials."""
        login_url = f"{self.base_url}/login/"

        # Step 1: GET /login/ to receive csrftoken cookie
        opener.open(urllib.request.Request(login_url))

        csrf_token = None
        for cookie in cookie_jar:
            if cookie.name == "csrftoken":
                csrf_token = cookie.value
                break

        if not csrf_token:
            raise RuntimeError(
                "Login failed: no CSRF token received from GET /login/. "
                "Check that base_url is correct in credentials.local."
            )

        # Step 2: POST /login/ with CSRF token + credentials
        form_data = urllib.parse.urlencode({
            "csrfmiddlewaretoken": csrf_token,
            "email": self.username,
            "password": self.password,
        }).encode()

        req = urllib.request.Request(
            login_url,
            data=form_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_url,
            },
        )
        opener.open(req)

        # Verify login succeeded by checking for sessionid cookie
        has_session = any(c.name == "sessionid" for c in cookie_jar)
        if not has_session:
            raise RuntimeError(
                "Login failed: no session cookie received. "
                "Check username and password in credentials.local."
            )


class OIDCDiscovery:
    """Fetch and cache the OpenID Connect discovery document."""

    def __init__(self, base_url: str, ssl_context: ssl.SSLContext | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._ssl_context = ssl_context
        self._doc: dict | None = None

    def _fetch(self) -> dict:
        if self._doc is not None:
            return self._doc
        url = f"{self.base_url}/.well-known/oauth-authorization-server"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, context=self._ssl_context)
        self._doc = json.loads(resp.read().decode())
        return self._doc

    @property
    def authorization_endpoint(self) -> str:
        return self._fetch()["authorization_endpoint"]

    @property
    def token_endpoint(self) -> str:
        return self._fetch()["token_endpoint"]


class OAuthAuth:
    """OAuth 2.0 Authorization Code + PKCE flow."""

    REDIRECT_URI = "http://127.0.0.1:18722/callback"
    LISTEN_PORT = 18722
    BROWSER_TIMEOUT = 120

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str = "",
        scopes: str = "openid profile email",
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self._ssl_context = ssl_context
        self._discovery = OIDCDiscovery(self.base_url, ssl_context=ssl_context)
        self._cache = TokenCache()

    # --- Public API ---

    def _generate_pkce_and_auth_url(self) -> tuple[str, str, str]:
        """Generate PKCE values and return (auth_url, code_verifier, state)."""
        code_verifier = secrets.token_urlsafe(96)  # ~128 chars
        code_challenge = (
            urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        state = secrets.token_urlsafe(32)

        auth_params = urllib.parse.urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.REDIRECT_URI,
            "scope": self.scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })
        auth_url = f"{self._discovery.authorization_endpoint}?{auth_params}"
        return auth_url, code_verifier, state

    def _exchange_code(self, code: str, code_verifier: str) -> TokenEntry:
        """Exchange an authorization code for tokens and cache the result."""
        token_data = self._token_request({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.REDIRECT_URI,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        })

        entry = TokenEntry(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=time.time() + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
        )
        self._cache.put(self.base_url, entry)
        return entry

    def authorize_interactive(self) -> TokenEntry:
        """Run the full browser-based OAuth flow with local callback server."""
        auth_url, code_verifier, state = self._generate_pkce_and_auth_url()

        # Will be set by the callback handler
        result: dict = {}
        error: list[str] = []

        class _CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                params = dict(urllib.parse.parse_qsl(parsed.query))

                if params.get("error"):
                    error.append(f"{params['error']}: {params.get('error_description', '')}")
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization failed. You can close this tab.")
                    return

                if params.get("state") != state:
                    error.append("State mismatch — possible CSRF attack.")
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"State mismatch. You can close this tab.")
                    return

                result["code"] = params["code"]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login successful! You can close this tab.")

            def log_message(self, format: str, *args: object) -> None:
                pass  # suppress request logs

        server = http.server.HTTPServer(("127.0.0.1", self.LISTEN_PORT), _CallbackHandler)
        server.timeout = self.BROWSER_TIMEOUT

        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        print(f"Opening browser for login...\n  {auth_url}", file=sys.stderr)
        webbrowser.open(auth_url)

        server_thread.join(timeout=self.BROWSER_TIMEOUT)
        server.server_close()

        if error:
            raise RuntimeError(f"OAuth authorization failed: {error[0]}")
        if "code" not in result:
            raise RuntimeError(
                "OAuth authorization timed out — no callback received within "
                f"{self.BROWSER_TIMEOUT}s. Check your browser."
            )

        return self._exchange_code(result["code"], code_verifier)

    def start_manual_flow(self) -> str:
        """Start OAuth flow for non-interactive environments.

        Generates PKCE values, persists them to the token cache under a
        _pending:<base_url> key, and returns the authorization URL.
        """
        auth_url, code_verifier, state = self._generate_pkce_and_auth_url()

        # Persist pending flow data so complete_manual_flow() can pick it up
        pending_key = f"_pending:{self.base_url}"
        pending_entry = TokenEntry(
            access_token=code_verifier,  # stash code_verifier here
            refresh_token=state,          # stash state here
            expires_at=time.time() + 600, # 10 min to complete
            token_type="pending",
        )
        self._cache.put(pending_key, pending_entry)

        return auth_url

    def complete_manual_flow(self, code: str) -> TokenEntry:
        """Complete OAuth flow by exchanging an authorization code for tokens.

        Accepts either a bare authorization code or a full redirect URL like
        ``http://127.0.0.1:18722/callback?code=ABC&state=XYZ``.

        Reads back the pending code_verifier and state from cache,
        exchanges the code, caches the tokens, and removes the pending entry.
        """
        pending_key = f"_pending:{self.base_url}"
        pending = self._cache.get(pending_key)

        if pending is None or pending.token_type != "pending":
            raise RuntimeError(
                "No pending login flow found. Run 'setup login' first (without --code) "
                "to start the flow."
            )

        if pending.is_expired(margin_seconds=0):
            self._cache.remove(pending_key)
            raise RuntimeError(
                "Pending login flow has expired. Run 'setup login' again to start a new flow."
            )

        # If the input looks like a URL, extract the code (and validate state)
        if code.startswith("http"):
            parsed = urllib.parse.urlparse(code)
            params = dict(urllib.parse.parse_qsl(parsed.query))
            if "code" not in params:
                raise RuntimeError(
                    "URL does not contain a 'code' parameter. "
                    "Paste the full redirect URL or just the authorization code."
                )
            # Validate state if present in the URL
            expected_state = pending.refresh_token  # state was stashed here
            url_state = params.get("state")
            if url_state and url_state != expected_state:
                self._cache.remove(pending_key)
                raise RuntimeError(
                    "State mismatch — the URL does not match the pending login flow. "
                    "Run 'setup login' again to start a new flow."
                )
            code = params["code"]

        code_verifier = pending.access_token
        entry = self._exchange_code(code, code_verifier)
        self._cache.remove(pending_key)
        return entry

    def get_valid_token(self) -> TokenEntry | None:
        """Return a valid token from cache, refreshing if needed. None if unavailable."""
        entry = self._cache.get(self.base_url)
        if entry is None:
            return None

        if not entry.is_expired():
            return entry

        if entry.refresh_token:
            try:
                return self._refresh_token(entry.refresh_token)
            except Exception:
                self._cache.remove(self.base_url)
                return None

        self._cache.remove(self.base_url)
        return None

    # --- Internal ---

    def _refresh_token(self, refresh_token_value: str) -> TokenEntry:
        token_data = self._token_request({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_value,
            "client_id": self.client_id,
        })
        entry = TokenEntry(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", refresh_token_value),
            expires_at=time.time() + token_data.get("expires_in", 3600),
            token_type=token_data.get("token_type", "Bearer"),
        )
        self._cache.put(self.base_url, entry)
        return entry

    def _token_request(self, data: dict) -> dict:
        """POST to the token endpoint and return the JSON response."""
        if self.client_secret:
            data["client_secret"] = self.client_secret
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            self._discovery.token_endpoint,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = urllib.request.urlopen(req, context=self._ssl_context)
        return json.loads(resp.read().decode())

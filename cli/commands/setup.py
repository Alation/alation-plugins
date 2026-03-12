"""Setup and authentication commands."""

import json
import os
import ssl
import urllib.error
from pathlib import Path
from typing import Any

from cli.clients.auth import OAuthAuth
from cli.clients.base import AuthenticationError
from cli.clients.config import ConfigAPIClient
from cli.clients.credentials import (
    find_credentials_file,
    load_credentials,
    parse_credentials_file,
    save_credentials,
)
from cli.clients.token_cache import TokenCache


def register(group_parsers):
    parser = group_parsers.add_parser("setup", help="Setup and authentication")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Check setup status (JSON output)").set_defaults(func=cmd_check)

    cred_p = sub.add_parser("credentials", help="Create or update credentials.local")
    cred_p.add_argument("--base_url", required=True, help="Alation instance URL")
    cred_p.add_argument("--username", help="Username for password auth")
    cred_p.add_argument("--password", help="Password for password auth")
    cred_p.add_argument("--client_id", help="OAuth client ID")
    cred_p.add_argument("--client_secret", help="OAuth client secret")
    cred_p.add_argument("--disable_ssl_verification", action="store_true", help="Disable SSL verification")
    cred_p.add_argument("--force", action="store_true", help="Overwrite existing credentials with different base_url")
    cred_p.set_defaults(func=cmd_credentials)

    login_p = sub.add_parser("login", help="Authenticate with Alation")
    login_p.add_argument("--cowork", action="store_true", help="Use manual OAuth flow (no local browser)")
    login_p.add_argument(
        "--code",
        help="Authorization code or full redirect URL from manual OAuth flow",
    )
    login_p.set_defaults(func=cmd_login)


def _build_check_result() -> dict:
    """Build the structured check result dict."""
    creds_info: dict[str, Any] = {
        "found": False,
        "path": None,
        "auth_method": None,
        "base_url": None,
        "has_client_id": False,
        "has_client_secret": False,
        "has_username": False,
        "has_password": False,
    }
    token_info: dict[str, Any] = {
        "found": False,
        "expired": None,
        "expires_at": None,
    }
    api_info: dict[str, Any] = {
        "reachable": None,
        "authenticated": None,
        "error": None,
    }
    result: dict[str, Any] = {
        "credentials_file": creds_info,
        "token": token_info,
        "api": api_info,
        "environment": {
            "container": _is_cowork_container(),
        },
        "ready": False,
    }

    # Check credentials file
    creds_path = find_credentials_file()
    if creds_path is None:
        return result

    result["credentials_file"]["found"] = True
    result["credentials_file"]["path"] = str(creds_path)

    try:
        creds = load_credentials("alation")
    except (FileNotFoundError, ValueError) as e:
        result["api"]["error"] = str(e)
        return result

    base_url = creds.get("base_url", "").rstrip("/")
    has_client_id = bool(creds.get("client_id", ""))
    has_client_secret = bool(creds.get("client_secret", ""))
    has_username = bool(creds.get("username", ""))
    has_password = bool(creds.get("password", ""))

    if has_client_id:
        auth_method = "oauth"
    elif has_username:
        auth_method = "password"
    else:
        auth_method = None

    result["credentials_file"].update({
        "auth_method": auth_method,
        "base_url": base_url or None,
        "has_client_id": has_client_id,
        "has_client_secret": has_client_secret,
        "has_username": has_username,
        "has_password": has_password,
    })

    # Check cached token (OAuth only)
    if auth_method == "oauth" and base_url:
        cache = TokenCache()
        entry = cache.get(base_url)
        if entry and entry.token_type != "pending":
            result["token"]["found"] = True
            result["token"]["expired"] = entry.is_expired()
            result["token"]["expires_at"] = entry.expires_at

    # Check API reachability and authentication
    if base_url:
        try:
            with ConfigAPIClient() as client:
                client.list_agents(limit=1)
            result["api"]["reachable"] = True
            result["api"]["authenticated"] = True
            result["ready"] = True
        except AuthenticationError as e:
            result["api"]["reachable"] = True
            result["api"]["authenticated"] = False
            result["api"]["error"] = str(e)
        except urllib.error.URLError as e:
            result["api"]["reachable"] = False
            result["api"]["authenticated"] = False
            result["api"]["error"] = str(e)
        except Exception as e:  # noqa: BLE001
            result["api"]["error"] = str(e)

    return result


def cmd_check(_args) -> int:
    """Check setup status and return structured JSON. Always exits 0."""
    result = _build_check_result()
    print(json.dumps(result, indent=2))
    return 0


def _is_cowork_container() -> bool:
    """Detect whether we're running in a Cowork container where localhost isn't shared."""
    if os.environ.get("CLAUDE_CODE_IS_COWORK"):
        return True
    return False


def _error_json(error: str, message: str, action: str) -> str:
    return json.dumps({"error": error, "message": message, "action": action}, indent=2)


def cmd_credentials(args) -> int:
    """Create or update credentials.local."""
    # Build values dict from args
    values: dict[str, str] = {"base_url": args.base_url.rstrip("/")}
    if args.username:
        values["username"] = args.username
    if args.password:
        values["password"] = args.password
    if args.client_id:
        values["client_id"] = args.client_id
    if args.client_secret:
        values["client_secret"] = args.client_secret
    if args.disable_ssl_verification:
        values["disable_ssl_verification"] = "true"

    # Determine target path and check for conflicts
    existing_path = find_credentials_file()
    if existing_path:
        data = parse_credentials_file(existing_path)
        existing_base_url = (
            data.get("services", {}).get("alation", {}).get("base_url", "").rstrip("/")
        )
        if existing_base_url and existing_base_url != values["base_url"] and not args.force:
            print(_error_json(
                "base_url_mismatch",
                f"Existing credentials.local at {existing_path} is configured for "
                f"'{existing_base_url}' but you provided '{values['base_url']}'. "
                f"Use --force to overwrite.",
                f"Re-run with --force to overwrite: python -m cli setup credentials "
                f"--base_url {values['base_url']} ... --force",
            ))
            return 1
        target_path = existing_path
    else:
        if _is_cowork_container():
            mnt = Path.home() / "mnt"
            writable_dir = None
            if mnt.is_dir():
                for child in sorted(mnt.iterdir()):
                    if child.is_dir() and child.name != "uploads" and not child.name.startswith("."):
                        writable_dir = child
                        break
            target_path = (writable_dir or Path.cwd()) / "credentials.local"
        else:
            target_path = Path.cwd() / "credentials.local"

    try:
        save_credentials("alation", values, target_path)
    except PermissionError:
        print(_error_json(
            "permission_denied",
            f"Cannot write to {target_path}: permission denied.",
            f"Check file permissions on {target_path}, or specify a different location.",
        ))
        return 1

    print(json.dumps({"status": "ok", "path": str(target_path)}, indent=2))
    return 0


def cmd_login(args) -> int:
    """Authenticate with Alation via OAuth or password."""
    # Load credentials
    try:
        creds = load_credentials("alation")
    except (FileNotFoundError, ValueError):
        print(_error_json(
            "credentials_not_found",
            "No credentials.local file found. The CLI needs credentials to connect to Alation.",
            "Run: python -m cli setup credentials --base_url <ALATION_URL> --client_id <ID> "
            "(for OAuth) or --username <USER> --password <PASS> (for password auth)",
        ))
        return 1

    base_url = creds.get("base_url", "").rstrip("/")
    if not base_url:
        print(_error_json(
            "missing_base_url",
            "credentials.local exists but base_url is empty.",
            "Run: python -m cli setup credentials --base_url <ALATION_URL> ... to set the base URL",
        ))
        return 1

    # Determine auth method
    client_id = creds.get("client_id", "")
    has_username = bool(creds.get("username", ""))

    if client_id:
        auth_method = "oauth"
    elif has_username:
        auth_method = "password"
    else:
        print(_error_json(
            "no_auth_method",
            "credentials.local has base_url but neither client_id (for OAuth) "
            "nor username (for password auth). Cannot authenticate.",
            f"Run: python -m cli setup credentials --base_url {base_url} --client_id <ID> "
            "(for OAuth) or --username <USER> --password <PASS> (for password auth)",
        ))
        return 1

    if auth_method == "oauth":
        client_secret = creds.get("client_secret", "")

        # Build SSL context if needed
        ssl_context = None
        if creds.get("disable_ssl_verification", "").lower() in ("1", "true", "yes"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        oauth = OAuthAuth(
            base_url,
            client_id,
            client_secret,
            ssl_context=ssl_context,
        )

        try:
            if args.cowork and args.code:
                # Complete manual flow with authorization code
                oauth.complete_manual_flow(args.code)
            elif args.cowork:
                # Start manual flow — return URL as JSON and exit
                auth_url = oauth.start_manual_flow()
                print(json.dumps({
                    "status": "pending",
                    "auth_url": auth_url,
                    "message": "Open auth_url in a browser and authorize the application.",
                    "next_step": 'After authorizing, run: python -m cli setup login --cowork --code "<REDIRECT_URL>"',
                }, indent=2))
                return 0
            else:
                # Interactive browser flow
                oauth.authorize_interactive()
        except OSError as e:
            if "Address already in use" in str(e):
                print(_error_json(
                    "port_in_use",
                    f"Port {OAuthAuth.LISTEN_PORT} is already in use. "
                    "Another login process may be running.",
                    f"Kill the process using port {OAuthAuth.LISTEN_PORT} and retry: "
                    "python -m cli setup login",
                ))
                return 1
            raise
        except RuntimeError as e:
            print(_error_json(
                "oauth_failed",
                f"OAuth authentication failed: {e}",
                "Check that client_id and client_secret are correct, then retry: "
                "python -m cli setup login" + (" --cowork" if args.cowork else ""),
            ))
            return 1

    # Password auth: no explicit login step needed, fall through to check

    # Final validation
    result = _build_check_result()
    print(json.dumps(result, indent=2))
    return 0

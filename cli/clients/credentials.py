"""Load credentials from credentials.local YAML file.

Replaces the old .env-based credential loading with a single
credentials.local file (skill-builder convention).
"""

from __future__ import annotations

from pathlib import Path


def find_credentials_file() -> Path | None:
    """Find an existing credentials.local file, or return None if not found."""
    try:
        return _find_credentials_file()
    except FileNotFoundError:
        return None


def _find_credentials_file() -> Path:
    """Walk up from cwd (max 10 levels) to find credentials.local."""
    current = Path.cwd()
    for _ in range(10):
        candidate = current / "credentials.local"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: check home directory
    home_candidate = Path.home() / "credentials.local"
    if home_candidate.is_file():
        return home_candidate

    # Fallback: check ~/mnt and one level below (Cowork mounted directories)
    # In Cowork, HOME is /sessions/<random-name> and mounts are at ~/mnt/<project>/
    mnt_dir = Path.home() / "mnt"
    if mnt_dir.is_dir():
        # Check ~/mnt/credentials.local
        mnt_candidate = mnt_dir / "credentials.local"
        if mnt_candidate.is_file():
            return mnt_candidate
        # Check ~/mnt/*/credentials.local (one level down)
        for child in mnt_dir.iterdir():
            if child.is_dir():
                child_candidate = child / "credentials.local"
                if child_candidate.is_file():
                    return child_candidate

    raise FileNotFoundError(
        "credentials.local not found. "
        "Copy credentials.local.example to credentials.local and fill in your values."
    )


def _parse_yaml(text: str) -> dict:
    """Minimal YAML parser for simple nested key: value structures.

    Handles:
    - Top-level and nested keys with 2-space indent
    - Quoted and unquoted string values
    - Comments and blank lines
    """
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]

    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)

        # Pop stack back to parent level
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        colon_pos = stripped.find(":")
        if colon_pos == -1:
            continue

        key = stripped[:colon_pos].strip()
        value_part = stripped[colon_pos + 1 :].strip()

        # Remove inline comments (only if preceded by space)
        comment_pos = value_part.find(" #")
        if comment_pos != -1:
            value_part = value_part[:comment_pos].strip()

        parent = stack[-1][1]

        if value_part:
            # Strip surrounding quotes
            if len(value_part) >= 2 and value_part[0] == value_part[-1] and value_part[0] in ('"', "'"):
                value_part = value_part[1:-1]
            parent[key] = value_part
        else:
            # Nested mapping
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))

    return root


def load_credentials(service_name: str) -> dict:
    """Load credentials for a named service from credentials.local.

    Returns the service's key-value dict (e.g. base_url, username, password).
    """
    path = _find_credentials_file()
    text = path.read_text()
    data = _parse_yaml(text)

    services = data.get("services")
    if not isinstance(services, dict):
        raise ValueError(f"credentials.local missing 'services' section (found in {path})")

    service = services.get(service_name)
    if not isinstance(service, dict):
        raise ValueError(
            f"credentials.local missing 'services.{service_name}' section (found in {path})"
        )

    return service


def _serialize_yaml(data: dict, indent: int = 0) -> str:
    """Inverse of _parse_yaml. Recursively writes nested dicts with 2-space indent.

    Quote leaf values that contain '#' or ': ' to avoid parse ambiguity.
    """
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_serialize_yaml(value, indent + 1))
        else:
            s = str(value)
            if "#" in s or ": " in s or s == "":
                s = f'"{s}"'
            lines.append(f"{prefix}{key}: {s}")
    return "\n".join(lines)


def parse_credentials_file(path: Path) -> dict:
    """Read a credentials file at path and return parsed dict."""
    return _parse_yaml(path.read_text())


def save_credentials(service_name: str, values: dict, path: Path) -> Path:
    """Create or update a credentials file, merging into services.<service_name>.

    If path exists, parses it and merges. Otherwise creates fresh structure.
    Returns the path written.
    """
    if path.exists():
        data = _parse_yaml(path.read_text())
    else:
        data = {}

    services = data.get("services")
    if not isinstance(services, dict):
        services = {}
        data["services"] = services

    existing_service = services.get(service_name)
    if isinstance(existing_service, dict):
        existing_service.update(values)
    else:
        services[service_name] = dict(values)

    path.write_text(_serialize_yaml(data) + "\n")
    return path

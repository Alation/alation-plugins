"""Shared helpers for CLI commands."""

import json
import sys

from cli.clients.base import print_error


def resolve_positional_or_flag(args, positional: str, flag: str, label: str) -> str:
    """Return whichever of the positional arg or --flag was provided, or exit."""
    val = getattr(args, positional, None) or getattr(args, flag, None)
    if not val:
        print_error(f"{label} is required")
        sys.exit(2)
    return val


def read_json_stdin(description: str = "JSON") -> dict | None:
    """Read a JSON object from stdin. Returns None (after printing error) on failure."""
    if sys.stdin.isatty():
        print_error(f"No {description} on stdin. Pipe input, e.g.: echo '{{...}}' | python -m cli ...")
        return None
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON input: {e}")
        return None
    if not isinstance(data, dict):
        print_error(f"Expected a JSON object for {description}, got {type(data).__name__}")
        return None
    return data

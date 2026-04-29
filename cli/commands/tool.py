"""Tool configuration and invocation commands."""

import json
import sys
import urllib.error

from cli.clients.base import print_json, print_error
from cli.clients.config import ConfigAPIClient, _extract_items
from cli.clients.chat import ChatClient, MessagePart, _is_config_id
from cli.commands._helpers import read_json_stdin

THINKING_PREVIEW_LEN = 100


def register(group_parsers):
    parser = group_parsers.add_parser("tool", help="Manage and invoke tools")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List tool configs").set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get tool config by ID")
    get_p.add_argument("id", help="Tool config ID")
    get_p.set_defaults(func=cmd_get)

    schema_p = sub.add_parser("schema", help="Get tool schema by reference")
    schema_p.add_argument("tool_ref", help="Tool reference name or UUID")
    schema_p.set_defaults(func=cmd_schema)

    sub.add_parser("create", help="Create tool config (read JSON from stdin)").set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update tool config (read JSON from stdin)")
    update_p.add_argument("id", help="Tool config ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete tool config")
    delete_p.add_argument("id", help="Tool config ID")
    delete_p.set_defaults(func=cmd_delete)

    call_p = sub.add_parser("call", help="Invoke tool (streaming, JSON params on stdin)")
    call_p.add_argument("tool_ref", help="Tool reference name or UUID")
    call_p.add_argument("--chat-id", help="Existing chat ID to use")
    call_p.set_defaults(func=cmd_call)

    call_async_p = sub.add_parser("call-async", help="Invoke tool (async job, JSON params on stdin)")
    call_async_p.add_argument("tool_ref", help="Tool reference name or UUID")
    call_async_p.add_argument("--chat-id", help="Existing chat ID to use")
    call_async_p.set_defaults(func=cmd_call_async)


def _summarize_tool(tool: dict) -> dict:
    return {
        "id": tool.get("id"),
        "name": tool.get("name"),
        "function_name": tool.get("function_name"),
        "description": tool.get("description"),
        "tool_type": tool.get("tool_type"),
        "is_default": tool.get("is_default", False),
        "default_ref": tool.get("default_ref"),
        "url": tool.get("url"),
    }


def cmd_list(_args) -> int:
    with ConfigAPIClient() as client:
        result = client.list_tools()
        tools = _extract_items(result)
        print_json([_summarize_tool(t) for t in tools])
    return 0


def cmd_get(args) -> int:
    with ConfigAPIClient() as client:
        result = client.get_tool(args.id)
        print_json(result)
    return 0


def cmd_schema(args) -> int:
    with ConfigAPIClient() as client:
        if _is_config_id(args.tool_ref):
            result = client.get_tool(args.tool_ref)
        else:
            result = client.get_default_tool(args.tool_ref)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    config = read_json_stdin("tool config")
    if config is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.create_tool(config)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    updates = read_json_stdin("tool config")
    if updates is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.update_tool(args.id, updates)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with ConfigAPIClient() as client:
        client.delete_tool(args.id)
        print(f"Deleted tool config: {args.id}")
    return 0


def _read_params_from_stdin() -> dict:
    """Read JSON parameters from stdin."""
    if sys.stdin.isatty():
        print_error("No input provided. Pipe JSON parameters via stdin.")
        print_error('Example: echo \'{"query": "sales"}\' | python -m cli tool call search_catalog_tool')
        sys.exit(1)
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON input: {e}")
        sys.exit(1)


def _process_tool_return_part(part: MessagePart) -> None:
    """Process and print a tool return part."""
    content = part.content
    if content:
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            print_json(parsed)
        except (json.JSONDecodeError, TypeError):
            print(content)
    if part.metadata:
        print("\nMetadata:", file=sys.stderr)
        print_json(part.metadata)


def _process_stream_part(part: MessagePart) -> None:
    """Process a single message part from the stream."""
    if part.kind == "text":
        print(part.content)
    elif part.kind == "thinking":
        preview = part.content[:THINKING_PREVIEW_LEN]
        print(f"[Thinking: {preview}...]", file=sys.stderr)
    elif part.kind == "tool-call":
        print(f"[Tool Call: {part.tool_name}]", file=sys.stderr)
    elif part.kind in ("tool-return", "builtin-tool-return"):
        _process_tool_return_part(part)


def cmd_call(args) -> int:
    params = _read_params_from_stdin()
    with ChatClient() as client:
        found_chat_id = None
        try:
            for message in client.invoke_tool_stream(args.tool_ref, params, args.chat_id):
                if message.chat_id and not found_chat_id:
                    found_chat_id = message.chat_id
                    print(f"Chat ID: {found_chat_id}", file=sys.stderr)
                for part in message.parts:
                    _process_stream_part(part)
        except urllib.error.HTTPError as e:
            print_error(f"Failed to invoke tool: {e}")
            return 1
    return 0


def cmd_call_async(args) -> int:
    params = _read_params_from_stdin()
    with ChatClient() as client:
        try:
            result = client.invoke_tool_async(args.tool_ref, params, args.chat_id)
            print_json(result)
        except urllib.error.HTTPError as e:
            print_error(f"Failed to invoke tool: {e}")
            return 1
    return 0

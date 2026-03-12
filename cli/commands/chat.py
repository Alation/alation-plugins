"""Chat with AI agents commands."""

import json
import sys
import urllib.error
from typing import Any

from cli.clients.base import print_error, print_json
from cli.clients.chat import ChatClient, MessagePart

THINKING_PREVIEW_LEN = 100


def register(group_parsers):
    parser = group_parsers.add_parser("chat", help="Chat with AI agents")
    sub = parser.add_subparsers(dest="command", required=True)

    send_p = sub.add_parser("send", help="Chat with agent (streaming, JSON on stdin)")
    send_p.add_argument("agent_ref", help="Agent reference name or UUID")
    send_p.add_argument("--chat-id", help="Existing chat ID to continue")
    send_p.set_defaults(func=cmd_send)

    cancel_p = sub.add_parser("cancel", help="Cancel a running chat")
    cancel_p.add_argument("chat_id", help="Chat ID to cancel")
    cancel_p.set_defaults(func=cmd_cancel)

    messages_p = sub.add_parser("messages", help="Get chat messages")
    messages_p.add_argument("chat_id", help="Chat ID")
    messages_p.add_argument("--limit", type=int, default=100, help="Max messages")
    messages_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    messages_p.set_defaults(func=cmd_messages)

    history_p = sub.add_parser("history", help="List recent chats")
    history_p.add_argument("--limit", type=int, default=20, help="Max chats")
    history_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    history_p.set_defaults(func=cmd_history)


def _process_chat_part(part: MessagePart) -> dict[str, Any] | None:
    """Process a message part and return pending approval info if any."""
    if part.kind == "text":
        print(part.content)
    elif part.kind == "thinking":
        preview = part.content[:THINKING_PREVIEW_LEN]
        ellipsis = "..." if len(part.content) > THINKING_PREVIEW_LEN else ""
        print(f"[Thinking: {preview}{ellipsis}]", file=sys.stderr)
    elif part.kind == "tool-call":
        print(f"[Tool Call: {part.tool_name}]", file=sys.stderr)
        raw = part.raw
        if raw.get("pending_approval"):
            return {
                "tool_name": part.tool_name,
                "args": part.tool_args,
            }
    elif part.kind in ("tool-return", "builtin-tool-return"):
        print(f"[Tool Complete: {part.tool_name}]", file=sys.stderr)
    return None


def _read_payload_from_stdin() -> dict:
    """Read JSON payload from stdin."""
    if sys.stdin.isatty():
        print_error("No input provided. Pipe JSON payload via stdin.")
        print_error(
            'Example: echo \'{"message": "Find sales data"}\' | '
            "python -m cli chat send catalog_search_agent"
        )
        sys.exit(1)
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON input: {e}")
        sys.exit(1)


def cmd_send(args) -> int:
    payload = _read_payload_from_stdin()
    with ChatClient() as client:
        found_chat_id = None
        pending_tool_calls: dict[str, dict] = {}

        try:
            for message in client.chat_agent_stream(args.agent_ref, payload, args.chat_id):
                if message.chat_id and not found_chat_id:
                    found_chat_id = message.chat_id
                    print(f"Chat ID: {found_chat_id}", file=sys.stderr)

                if message.kind == "response":
                    for part in message.parts:
                        pending_info = _process_chat_part(part)
                        if pending_info and part.tool_call_id:
                            pending_tool_calls[part.tool_call_id] = pending_info

            if pending_tool_calls:
                print("\nPending Tool Approvals:", file=sys.stderr)
                for call_id, info in pending_tool_calls.items():
                    print(f"  {call_id}: {info['tool_name']}", file=sys.stderr)

        except urllib.error.HTTPError as e:
            print_error(f"Failed to chat with agent: {e}")
            return 1
    return 0


def cmd_cancel(args) -> int:
    with ChatClient() as client:
        try:
            result = client.cancel_chat(args.chat_id)
            print_json(result)
        except urllib.error.HTTPError as e:
            print_error(f"Failed to cancel chat: {e}")
            return 1
    return 0


def cmd_messages(args) -> int:
    with ChatClient() as client:
        try:
            result = client.get_chat_messages(args.chat_id, args.limit, args.skip)
            print_json(result)
        except urllib.error.HTTPError as e:
            print_error(f"Failed to get messages: {e}")
            return 1
    return 0


def cmd_history(args) -> int:
    with ChatClient() as client:
        try:
            result = client.list_chats(args.limit, args.skip)
            print_json(result)
        except urllib.error.HTTPError as e:
            print_error(f"Failed to list chats: {e}")
            return 1
    return 0

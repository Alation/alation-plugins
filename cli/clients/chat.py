"""Client for Alation AI chat and tool invocation APIs.

Extends AlationClient for chatting with agents, invoking tools,
streaming responses, and managing chat sessions.
"""

import json
import uuid
from collections.abc import Iterator
from typing import Any, cast

from .base import AlationClient


def _is_config_id(ref: str) -> bool:
    """Check if a reference is a config ID (UUID) vs a default ref name."""
    try:
        uuid.UUID(ref)
        return True
    except ValueError:
        return False


class SSEEvent:
    """Represents a Server-Sent Event."""

    def __init__(
        self,
        event: str | None = None,
        data: str | None = None,
        id: str | None = None,  # noqa: A002
        retry: int | None = None,
    ) -> None:
        self.event = event
        self.data = data
        self.id = id
        self.retry = retry

    def json(self) -> dict[str, Any]:
        """Parse the data field as JSON."""
        if self.data is None:
            return {}
        return cast("dict[str, Any]", json.loads(self.data))


class MessagePart:
    """Represents a part of a message (text, thinking, tool-call, tool-return)."""

    def __init__(self, part_data: dict[str, Any]) -> None:
        self._data = part_data

    @property
    def kind(self) -> str:
        """Get the part kind."""
        return str(self._data.get("part_kind", ""))

    @property
    def content(self) -> str:
        """Get the content (for text/thinking parts)."""
        return str(self._data.get("content", ""))

    @property
    def tool_name(self) -> str:
        """Get the tool name (for tool-call/tool-return parts)."""
        return str(self._data.get("tool_name", ""))

    @property
    def tool_args(self) -> str:
        """Get the tool arguments as string (for tool-call parts)."""
        return str(self._data.get("args", ""))

    @property
    def tool_call_id(self) -> str:
        """Get the tool call ID."""
        return str(self._data.get("tool_call_id", ""))

    @property
    def metadata(self) -> dict[str, Any] | None:
        """Get metadata (for tool-return parts)."""
        return self._data.get("metadata")

    @property
    def raw(self) -> dict[str, Any]:
        """Get the raw part data."""
        return self._data


class StreamMessage:
    """Represents a message from the chat stream."""

    def __init__(self, event_data: dict[str, Any]) -> None:
        self._data = event_data

    @property
    def chat_id(self) -> str | None:
        """Get the chat ID if present."""
        return self._data.get("chat_id")

    @property
    def message_id(self) -> str | None:
        """Get the message ID if present."""
        return self._data.get("id")

    @property
    def model_message(self) -> dict[str, Any] | None:
        """Get the model message if present."""
        return self._data.get("model_message")

    @property
    def kind(self) -> str | None:
        """Get the message kind (request/response)."""
        if self.model_message:
            return self.model_message.get("kind")
        return None

    @property
    def parts(self) -> list[MessagePart]:
        """Get the message parts."""
        if self.model_message:
            return [MessagePart(p) for p in self.model_message.get("parts", [])]
        return []

    @property
    def raw(self) -> dict[str, Any]:
        """Get the raw event data."""
        return self._data


class ChatClient(AlationClient):
    """Client for Alation AI chat APIs.

    Supports streaming conversations with agents, tool invocation,
    and tool approval workflows.

    Usage:
        with ChatClient() as client:
            for message in client.chat_agent_stream("sql_query_agent", payload):
                print(message.parts)
    """

    def _parse_sse_stream(self, response) -> Iterator[SSEEvent]:
        """Parse Server-Sent Events from a streaming response."""
        event = None
        data_lines: list[str] = []

        for raw_bytes in response:
            line = raw_bytes.decode("utf-8").strip()

            if not line:
                if data_lines:
                    yield SSEEvent(
                        event=event,
                        data="\n".join(data_lines),
                    )
                event = None
                data_lines = []
                continue

            if line.startswith(":"):
                continue

            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if data_lines:
            yield SSEEvent(event=event, data="\n".join(data_lines))

    def _stream_chat(
        self,
        path: str,
        payload: dict[str, Any],
        chat_id: str | None = None,
    ) -> Iterator[StreamMessage]:
        """Stream chat messages from an endpoint.

        Args:
            path: API path (e.g., /api/v1/chats/agent/default/sql_query_agent/stream)
            payload: Request payload
            chat_id: Optional existing chat ID to continue

        Yields:
            StreamMessage objects containing parsed message data
        """
        if not self._opener:
            raise RuntimeError("Client not initialized. Use 'with' context manager.")

        params = {}
        if chat_id:
            params["chat_id"] = chat_id

        response = self._stream_request("POST", path, json_data=payload, params=params, timeout=300)
        for sse_event in self._parse_sse_stream(response):
            if sse_event.data == "[DONE]":
                break
            if sse_event.data:
                try:
                    event_data = json.loads(sse_event.data)
                    yield StreamMessage(event_data)
                except json.JSONDecodeError:
                    continue

    # --- Tool Invocation API ---

    def invoke_tool_stream(
        self,
        tool_ref: str,
        params: dict[str, Any],
        chat_id: str | None = None,
    ) -> Iterator[StreamMessage]:
        """Invoke a tool with streaming output.

        Args:
            tool_ref: Tool reference name (e.g., "search_catalog_tool") or config ID (UUID)
            params: Tool parameters
            chat_id: Optional chat ID to continue

        Yields:
            StreamMessage objects
        """
        if _is_config_id(tool_ref):
            path = f"/api/v1/chats/tool/{tool_ref}/stream"
        else:
            path = f"/api/v1/chats/tool/default/{tool_ref}/stream"
        for msg in self._stream_chat(path, params, chat_id):
            yield msg

    def invoke_tool_async(
        self,
        tool_ref: str,
        params: dict[str, Any],
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool as an async job.

        Args:
            tool_ref: Tool reference name or config ID (UUID)
            params: Tool parameters
            chat_id: Optional chat ID to use

        Returns:
            Task info with task_id and chat_id
        """
        if _is_config_id(tool_ref):
            path = f"/api/v1/chats/tool/{tool_ref}/call"
        else:
            path = f"/api/v1/chats/tool/default/{tool_ref}/call"
        if chat_id:
            path = f"{path}?chat_id={chat_id}"
        result = self.post(path, params)
        return result or {}

    # --- Agent Chat API ---

    def chat_agent_stream(
        self,
        agent_ref: str,
        payload: dict[str, Any],
        chat_id: str | None = None,
    ) -> Iterator[StreamMessage]:
        """Chat with an agent with streaming output.

        Args:
            agent_ref: Agent reference name (e.g., "sql_query_agent") or config ID (UUID)
            payload: Agent input payload
            chat_id: Optional chat ID to continue

        Yields:
            StreamMessage objects
        """
        if _is_config_id(agent_ref):
            path = f"/api/v1/chats/agent/{agent_ref}/stream"
        else:
            path = f"/api/v1/chats/agent/default/{agent_ref}/stream"
        for msg in self._stream_chat(path, payload, chat_id):
            yield msg

    def chat_agent_async(
        self,
        agent_ref: str,
        payload: dict[str, Any],
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        """Chat with an agent as an async job.

        Args:
            agent_ref: Agent reference name or config ID (UUID)
            payload: Agent input payload
            chat_id: Optional chat ID to use

        Returns:
            Task info with task_id and chat_id
        """
        if _is_config_id(agent_ref):
            path = f"/api/v1/chats/agent/{agent_ref}/call"
        else:
            path = f"/api/v1/chats/agent/default/{agent_ref}/call"
        if chat_id:
            path = f"{path}?chat_id={chat_id}"
        result = self.post(path, payload)
        return result or {}

    # --- Chat Management API ---

    def create_chat(
        self, name: str | None = None, tags: list[str] | None = None
    ) -> dict[str, Any]:
        """Create a new chat."""
        data: dict[str, Any] = {}
        if name:
            data["name"] = name
        if tags:
            data["tags"] = tags
        result = self.post("/api/v1/chats", data)
        return result or {}

    def get_chat(self, chat_id: str) -> dict[str, Any]:
        """Get a chat by ID."""
        return self.get(f"/api/v1/chats/{chat_id}")

    def get_chat_messages(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get messages for a chat."""
        return self.get(
            f"/api/v1/chats/{chat_id}/messages",
            params={"limit": limit, "offset": offset},
        )

    def list_chats(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str = "user",
        include_tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """List chats."""
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "created_by": created_by,
        }
        if include_tags:
            params["include_tags"] = include_tags
        if exclude_tags:
            params["exclude_tags"] = exclude_tags
        return self.get("/api/v1/chats", params)

    def cancel_chat(self, chat_id: str) -> dict[str, Any]:
        """Cancel a running chat."""
        result = self.post(f"/api/v1/chats/{chat_id}/cancel")
        return result or {}

    def approve_tools(
        self,
        agent_ref: str,
        chat_id: str,
        tool_approvals: dict[str, bool],
        original_payload: dict[str, Any],
    ) -> Iterator[StreamMessage]:
        """Submit tool approvals for a pending chat.

        Args:
            agent_ref: Agent reference name
            chat_id: Chat UUID
            tool_approvals: Dict of tool_call_id -> approved (True/False)
            original_payload: The original input payload used for the chat

        Yields:
            StreamMessage objects as the agent continues
        """
        payload = {**original_payload, "tool_approvals": tool_approvals}
        if _is_config_id(agent_ref):
            path = f"/api/v1/chats/agent/{agent_ref}/stream"
        else:
            path = f"/api/v1/chats/agent/default/{agent_ref}/stream"
        for msg in self._stream_chat(path, payload, chat_id):
            yield msg

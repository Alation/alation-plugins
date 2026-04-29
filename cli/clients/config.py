"""Config API client for agent, tool, LLM, and credential management.

Extends AlationClient with domain-specific methods for the config APIs.
Used by agent-config, llm-config, and tool-config skills.
"""

from __future__ import annotations

from typing import Any, cast

from .base import AlationClient
from . import url_helper


def _extract_items(result: Any) -> list[dict]:
    """Return the list of items from a list-style API response.

    Handles both shapes the Alation API uses: ``{"data": [...]}`` (e.g.,
    ``/api/v1/config/agent``, ``/api/v1/config/tool``) and ``{"results": [...]}``.
    Falls back to a bare list, or empty list if neither shape matches.
    """
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("data", "results"):
            value = result.get(key)
            if isinstance(value, list):
                return value
    return []


class ConfigAPIClient(AlationClient):
    """HTTP client for Alation AI config APIs.

    Inherits authentication and HTTP plumbing from AlationClient.
    Adds domain methods for agents, tools, LLMs, and credentials.

    Usage:
        with ConfigAPIClient() as client:
            agents = client.list_agents()
    """

    # --- Agent Config API ---

    def list_agents(
        self,
        limit: int = 100,
        offset: int = 0,
        visibility_labels: list[str] | None = None,
    ) -> dict:
        """List agent configs."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if visibility_labels:
            params["visibility_labels"] = visibility_labels
        result = self.get("/api/v1/config/agent", params)
        for agent in _extract_items(result):
            if agent.get("id"):
                agent["url"] = url_helper.agent_url(agent["id"])
        return result

    def get_agent(self, agent_id: str) -> dict:
        """Get agent config by ID."""
        result = self.get(f"/api/v1/config/agent/{agent_id}")
        if isinstance(result, dict):
            result["url"] = url_helper.agent_url(agent_id)
        return result

    def get_default_agent(self, ref: str) -> dict:
        """Get default agent config by reference name."""
        result = self.get(f"/api/v1/config/agent/default/{ref}")
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.agent_url(result["id"])
        return result

    def create_agent(self, config: dict) -> dict[str, Any]:
        """Create a new agent config."""
        result = self.post("/api/v1/config/agent", config)
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.agent_url(result["id"])
        return cast("dict[str, Any]", result)

    def update_agent(self, agent_id: str, updates: dict) -> dict:
        """Update an agent config."""
        result = self.patch(f"/api/v1/config/agent/{agent_id}", updates)
        if isinstance(result, dict):
            result["url"] = url_helper.agent_url(agent_id)
        return result

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent config."""
        self.delete(f"/api/v1/config/agent/{agent_id}")

    def clone_agent(self, agent_id: str) -> dict[str, Any]:
        """Clone an agent config."""
        result = self.post(f"/api/v1/config/agent/{agent_id}/clone")
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.agent_url(result["id"])
        return cast("dict[str, Any]", result)

    def publish_agent_as_tool(self, agent_id: str) -> dict[str, Any]:
        """Publish an agent as a tool."""
        result = self.post(f"/api/v1/config/agent/{agent_id}/publish_as_tool")
        return cast("dict[str, Any]", result)

    def unpublish_agent_tool(self, agent_id: str) -> None:
        """Unpublish an agent's tool."""
        self.delete(f"/api/v1/config/agent/{agent_id}/unpublish_tool")

    # --- Tool Config API ---

    def list_tools(
        self,
        limit: int = 100,
        offset: int = 0,
        visibility_labels: list[str] | None = None,
    ) -> dict:
        """List tool configs."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if visibility_labels:
            params["visibility_labels"] = visibility_labels
        result = self.get("/api/v1/config/tool", params)
        for tool in _extract_items(result):
            if tool.get("id"):
                tool["url"] = url_helper.tool_url(tool["id"])
        return result

    def get_tool(self, tool_id: str) -> dict:
        """Get tool config by ID."""
        result = self.get(f"/api/v1/config/tool/{tool_id}")
        if isinstance(result, dict):
            result["url"] = url_helper.tool_url(tool_id)
        return result

    def get_default_tool(self, ref: str) -> dict:
        """Get default tool config by reference name."""
        result = self.get(f"/api/v1/config/tool/default/{ref}")
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.tool_url(result["id"])
        return result

    def create_tool(self, config: dict) -> dict[str, Any]:
        """Create a new tool config."""
        result = self.post("/api/v1/config/tool", config)
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.tool_url(result["id"])
        return cast("dict[str, Any]", result)

    def update_tool(self, tool_id: str, updates: dict) -> dict:
        """Update a tool config."""
        result = self.put(f"/api/v1/config/tool/{tool_id}", updates)
        if isinstance(result, dict):
            result["url"] = url_helper.tool_url(tool_id)
        return result

    def delete_tool(self, tool_id: str) -> None:
        """Delete a tool config."""
        self.delete(f"/api/v1/config/tool/{tool_id}")

    # --- LLM Config API ---

    def list_llms(
        self,
        limit: int = 100,
        offset: int = 0,
        visibility_labels: list[str] | None = None,
        llm_credentials_id: str | None = None,
    ) -> dict:
        """List LLM configs."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if visibility_labels:
            params["visibility_labels"] = visibility_labels
        if llm_credentials_id:
            params["llm_credentials_id"] = llm_credentials_id
        return self.get("/api/v1/config/llm", params)

    def get_llm(self, llm_id: str) -> dict:
        """Get LLM config by ID."""
        return self.get(f"/api/v1/config/llm/{llm_id}")

    def create_llm(self, config: dict) -> dict[str, Any]:
        """Create a new LLM config."""
        result = self.post("/api/v1/config/llm", config)
        return cast("dict[str, Any]", result)

    def update_llm(self, llm_id: str, updates: dict) -> dict:
        """Update an LLM config."""
        return self.patch(f"/api/v1/config/llm/{llm_id}", updates)

    def delete_llm(self, llm_id: str) -> None:
        """Delete an LLM config."""
        self.delete(f"/api/v1/config/llm/{llm_id}")

    # --- LLM Credentials API ---

    def list_credentials(self, skip: int = 0, limit: int = 100) -> dict:
        """List LLM credentials."""
        return self.get("/api/v1/llm_credentials", {"skip": skip, "limit": limit})

    def get_credentials(self, creds_id: str) -> dict:
        """Get LLM credentials by ID."""
        return self.get(f"/api/v1/llm_credentials/{creds_id}")

    def create_credentials(self, config: dict) -> dict[str, Any]:
        """Create new LLM credentials."""
        result = self.post("/api/v1/llm_credentials", config)
        return cast("dict[str, Any]", result)

    def update_credentials(self, creds_id: str, updates: dict) -> dict:
        """Update LLM credentials."""
        return self.patch(f"/api/v1/llm_credentials/{creds_id}", updates)

    def delete_credentials(self, creds_id: str) -> None:
        """Delete LLM credentials."""
        self.delete(f"/api/v1/llm_credentials/{creds_id}")

    def validate_credentials(
        self, creds_id: str, provider: str, model_name: str | None = None
    ) -> dict[str, Any]:
        """Validate LLM credentials."""
        data: dict[str, str] = {"provider": provider}
        if model_name:
            data["model_name"] = model_name
        result = self.post(f"/api/v1/llm_credentials/{creds_id}/validate", data)
        return cast("dict[str, Any]", result)

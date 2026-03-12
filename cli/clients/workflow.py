"""Workflow and schedule API client.

Extends AlationClient with domain methods for the workflow and schedule APIs.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any, cast

from .base import AlationClient, ERR_CLIENT_NOT_INIT
from . import url_helper


class WorkflowAPIClient(AlationClient):
    """HTTP client for Alation AI workflow and schedule APIs.

    Inherits authentication and HTTP plumbing from AlationClient.
    Credentials are loaded from credentials.local (services.alation section).

    Usage:
        with WorkflowAPIClient() as client:
            workflows = client.list_workflows()
            print(json.dumps(workflows, indent=2))
    """

    # --- Workflow API ---

    def list_workflows(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """List workflows."""
        result = self.get("/api/v1/workflow/", {"limit": limit, "offset": offset})
        for wf in result.get("results", result if isinstance(result, list) else []):
            if wf.get("id"):
                wf["url"] = url_helper.workflow_url(wf["id"])
        return result

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Get workflow by ID."""
        result = self.get(f"/api/v1/workflow/{workflow_id}/")
        if isinstance(result, dict):
            result["url"] = url_helper.workflow_url(workflow_id)
        return result

    def create_workflow(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Create a new workflow."""
        result = self.post("/api/v1/workflow/", workflow)
        if isinstance(result, dict) and result.get("id"):
            result["url"] = url_helper.workflow_url(result["id"])
        return cast("dict[str, Any]", result)

    def update_workflow(self, workflow_id: str, workflow: dict[str, Any]) -> dict[str, Any]:
        """Update a workflow."""
        result = self.put(f"/api/v1/workflow/{workflow_id}/", workflow)
        if isinstance(result, dict):
            result["url"] = url_helper.workflow_url(workflow_id)
        return result

    def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow."""
        self.delete(f"/api/v1/workflow/{workflow_id}/")

    def execute_workflow(
        self,
        workflow_id: str,
        parameters: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Execute a workflow and stream results.

        Args:
            workflow_id: Workflow ID to execute
            parameters: Optional workflow parameters
            dry_run: If True, validate without executing

        Yields:
            Event dictionaries from the execution stream
        """
        if not self._opener:
            raise RuntimeError(ERR_CLIENT_NOT_INIT)

        path = f"/api/v1/workflow/{workflow_id}/execute/"
        payload: dict[str, Any] = {}
        if parameters:
            payload["parameters"] = parameters
        if dry_run:
            payload["dry_run"] = True

        response = self._stream_request("POST", path, json_data=payload, timeout=300)
        for raw_bytes in response:
            line = raw_bytes.decode("utf-8").strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue

    def validate_workflow(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Validate a workflow definition without creating it.

        Returns validation result with any errors found.
        """
        result = self.post("/api/v1/workflow/validate/", workflow)
        return cast("dict[str, Any]", result) if result else {"valid": True}

    # --- Schedule API ---

    def list_schedules(
        self, workflow_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        """List schedules, optionally filtered by workflow."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if workflow_id:
            params["workflow_id"] = workflow_id
        result = self.get("/api/v1/workflow/schedules/", params)
        for sched in result.get("results", result if isinstance(result, list) else []):
            wid = sched.get("workflow_id")
            if wid:
                sched["workflow_url"] = url_helper.workflow_url(wid)
        return result

    def get_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Get schedule by ID."""
        result = self.get(f"/api/v1/workflow/schedules/{schedule_id}/")
        if isinstance(result, dict):
            wid = result.get("workflow_id")
            if wid:
                result["workflow_url"] = url_helper.workflow_url(wid)
        return result

    def create_schedule(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """Create a new schedule."""
        result = self.post("/api/v1/workflow/schedules/", schedule)
        if isinstance(result, dict):
            wid = result.get("workflow_id")
            if wid:
                result["workflow_url"] = url_helper.workflow_url(wid)
        return cast("dict[str, Any]", result)

    def update_schedule(self, schedule_id: str, schedule: dict[str, Any]) -> dict[str, Any]:
        """Update a schedule."""
        return self.put(f"/api/v1/workflow/schedules/{schedule_id}/", schedule)

    def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule."""
        self.delete(f"/api/v1/workflow/schedules/{schedule_id}/")

    def enable_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Enable a schedule."""
        return self.put(f"/api/v1/workflow/schedules/{schedule_id}/", {"enabled": True})

    def disable_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Disable a schedule."""
        return self.put(f"/api/v1/workflow/schedules/{schedule_id}/", {"enabled": False})

    # --- Auth Config API (for schedules) ---

    def list_auth_configs(self) -> list[dict[str, Any]]:
        """List auth configs available for scheduling."""
        result = self.get("/api/v1/auth_configs/")
        return cast("list[dict[str, Any]]", result.get("data", result.get("results", [])))

    def get_managed_auth_config(self) -> dict[str, Any] | None:
        """Get the user's MANAGED auth config for scheduling."""
        configs = self.list_auth_configs()
        for config in configs:
            if config.get("auth_type") == "MANAGED":
                return config
        return None

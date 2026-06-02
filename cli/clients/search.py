"""Client for catalog search.

Uses the tool-based search endpoint via the Alation AI API.
The tool endpoint is async: it returns a chat_id, then results
are retrieved by polling the chat messages for a tool-return part.
"""

import json
import time
from typing import Any

from .base import AlationClient

_MAX_POLL_ATTEMPTS = 10
_POLL_INTERVAL_SECONDS = 1.0


class SearchClient(AlationClient):
    """Client for searching the Alation catalog.

    Uses the search_catalog_tool endpoint via the Alation AI API.

    Usage:
        with SearchClient() as client:
            results = client.search("sales")
    """

    def search(
        self,
        query: str,
        limit: int = 50,
        object_types: list[str] | None = None,
        filters: list[dict[str, Any]] | None = None,
        ranges: list[dict[str, Any]] | None = None,
        starred: bool | None = None,
        watching: bool | None = None,
        recent: bool | None = None,
        domain_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search the catalog, returning results plus a UI table_view_url.

        Only includes a payload key when its argument was provided, so the
        server applies its own defaults for omitted params.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            object_types: Optional filter by object types. Accepted values for
                object_types are:
                    - table
                    - procedure
                    - function
                    - api_resource
                    - api_resource_field
                    - api_resource_folder
                    - article
                    - bi_field
                    - catalog_set
                    - column
                    - dataflow
                    - datasource
                    - doc_schema
                    - docstore_collection
                    - docstore_folder
                    - domain
                    - execution_result
                    - file
                    - filesystem
                    - glossary
                    - glossary_term
                    - glossary_v3
                    - group
                    - query_or_statement
                    - report_collection
                    - report_datasource
                    - report_object
                    - report_source
                    - schema
                    - tag
                    - thread
                    - conversation
                    - user
                    - value
                    - query
                    - documentation
                    - bi_report (dashboard/report: Looker Dashboard, Power BI Report, Tableau Dashboard)
                    - bi_folder
                    - bi_datasource (semantic layer: Looker Explore, Power BI Dataset, Tableau Datasource)
                    - policy
                    - business_policy
                    - policy_group
            filters: Optional list of {"filter_id", "filter_values"} facet filters.
            ranges: Optional list of {"field", "start", "end"} ISO date-range filters.
            starred: Filter to only bookmarked/starred items when True.
            watching: Filter to only watched items when True.
            recent: Filter to only recently-visited items when True.
            domain_ids: Optional list of domain IDs to scope results.

        Returns:
            {"results": [...], "table_view_url": <str|None>} and, when the
            tool returned a plain-string status (no results / error / timeout),
            an additional "message" key.
        """
        payload: dict[str, Any] = {"search_term": query, "limit": limit}
        if object_types:
            payload["object_types"] = object_types
        if filters:
            payload["filters"] = filters
        if ranges:
            payload["ranges"] = ranges
        if starred is not None:
            payload["starred"] = starred
        if watching is not None:
            payload["watching"] = watching
        if recent is not None:
            payload["recent"] = recent
        if domain_ids:
            payload["domain_ids"] = domain_ids

        content, timed_out = self._call_tool_and_poll(
            "search_catalog_tool", payload
        )
        if timed_out:
            return {"results": [], "table_view_url": None, "message": self._timeout_message()}
        return self._extract_search_response(content)

    @staticmethod
    def _extract_search_response(content: str | None) -> dict[str, Any]:
        """Parse the search tool's tool-return content into {results, table_view_url}."""
        if content is None:
            return {"results": [], "table_view_url": None}
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Plain-string status, e.g. "No objects found for 'X'." or "Error: ..."
            return {"results": [], "table_view_url": None, "message": content}
        if isinstance(parsed, dict):
            return {
                "results": parsed.get("results", []),
                "table_view_url": parsed.get("table_view_url"),
            }
        if isinstance(parsed, list):
            return {"results": parsed, "table_view_url": None}
        # JSON scalar (string/number) — treat as a status message.
        return {"results": [], "table_view_url": None, "message": str(parsed)}

    def search_filter_fields(
        self, query: str, limit: int = 10
    ) -> dict[str, Any]:
        """Discover fields usable as search filters, ranked by similarity to query.

        Returns {"fields": [...]} or, on timeout/empty, a "message" key.
        """
        payload: dict[str, Any] = {"search_term": query, "limit": limit}
        content, timed_out = self._call_tool_and_poll(
            "get_search_filter_fields_tool", payload
        )
        if timed_out:
            return {"fields": [], "message": self._timeout_message()}
        return {"fields": self._extract_list(content)}

    def search_filter_values(
        self,
        field_id: int | str,
        query: str,
        limit: int = 10,
        is_builtin: bool = False,
    ) -> dict[str, Any]:
        """Resolve filter values (e.g. a data source name) to usable filter IDs.

        Returns {"values": [...]} or, on timeout/empty, a "message" key.
        """
        payload: dict[str, Any] = {
            "field_id": field_id,
            "search_term": query,
            "limit": limit,
            "is_builtin": is_builtin,
        }
        content, timed_out = self._call_tool_and_poll(
            "get_search_filter_values_tool", payload
        )
        if timed_out:
            return {"values": [], "message": self._timeout_message()}
        return {"values": self._extract_list(content)}

    @staticmethod
    def _extract_list(content: str | None) -> list[Any]:
        """Parse a tool-return whose content is a JSON list; [] on string/None."""
        if content is None:
            return []
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return []
        return parsed if isinstance(parsed, list) else []

    def _call_tool_and_poll(
        self, tool_ref: str, payload: dict[str, Any]
    ) -> tuple[str | None, bool]:
        """Invoke an async AI tool and poll its chat for the tool-return content.

        Returns:
            (content, timed_out). content is the raw tool-return string, or None
            if no tool-return part appeared. timed_out is True when polling
            exhausted all attempts without finding a tool-return.
        """
        result = self.post(
            f"/api/v1/chats/tool/default/{tool_ref}/call",
            payload,
        )
        chat_id = result["chat_id"]

        for _ in range(_MAX_POLL_ATTEMPTS):
            messages = self.get(f"/api/v1/chats/{chat_id}/messages") or {}
            for msg in messages.get("data", []):
                for part in msg.get("model_message", {}).get("parts", []):
                    if part.get("part_kind") == "tool-return":
                        return part.get("content"), False
            time.sleep(_POLL_INTERVAL_SECONDS)

        return None, True

    @staticmethod
    def _timeout_message() -> str:
        return (
            f"Tool timed out after ~{int(_MAX_POLL_ATTEMPTS * _POLL_INTERVAL_SECONDS)}s; "
            "the catalog tool may still be processing. Try again."
        )

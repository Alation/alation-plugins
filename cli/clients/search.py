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
    ) -> list[dict[str, Any]]:
        """Search the catalog for objects matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results
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
                    - bi_report
                    - bi_folder
                    - policy
                    - business_policy
                    - policy_group

        Returns:
            List of matching catalog objects with title, url, type, breadcrumbs
        """
        payload: dict[str, Any] = {
            "search_term": query,
            "limit": limit,
        }
        if object_types:
            payload["object_types"] = object_types

        # Trigger the async tool call
        result = self.post(
            "/api/v1/chats/tool/default/search_catalog_tool/call",
            payload,
        )
        chat_id = result["chat_id"]

        # Poll for the tool-return message containing results
        return self._poll_for_results(chat_id)

    def _poll_for_results(self, chat_id: str) -> list[dict[str, Any]]:
        """Poll chat messages until the tool-return with results is available."""
        for _ in range(_MAX_POLL_ATTEMPTS):
            messages = self.get(f"/api/v1/chats/{chat_id}/messages") or {}
            for msg in messages.get("data", []):
                for part in msg.get("model_message", {}).get("parts", []):
                    if part.get("part_kind") == "tool-return":
                        content = part.get("content", "[]")
                        try:
                            return json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            return []
            time.sleep(_POLL_INTERVAL_SECONDS)

        return []

"""Client for data product queries.

Extends AlationClient for querying data products:
- List and search products
- Execute SQL via streaming tool API
- Validate SQL queries
"""

import json
import re
import time
import uuid
from typing import Any, cast

from .base import AlationClient
from . import url_helper

_API_BASE = "/integration/data-products/api/v1"


class DataProductQueryClient(AlationClient):
    """Client for Data Products query operations.

    Handles authentication automatically via the parent AlationClient.
    Supports SSE streaming for SQL execution.

    Usage:
        with DataProductQueryClient() as client:
            products = client.list_products()
    """

    def _api_path(self, path: str) -> str:
        """Build full API path for data products endpoints."""
        return f"{_API_BASE}{path}"

    # --- Data Products API ---

    def search_products(self, query: str, marketplace_id: str) -> dict[str, Any]:
        """Search for data products using natural language.

        Args:
            query: Natural language search query
            marketplace_id: Marketplace identifier to search within
        """
        endpoint = self._api_path(f"/search-internally/{marketplace_id}/")
        result = self.post(endpoint, {"user_query": query})
        return cast("dict[str, Any]", result)

    def get_product(self, product_id: str, version_id: str | None = None) -> dict[str, Any]:
        """Get full data product details including schema.

        Args:
            product_id: Data product identifier
            version_id: Optional specific version to retrieve
        """
        if version_id:
            endpoint = self._api_path(f"/data-product/{product_id}/version/{version_id}/")
        else:
            endpoint = self._api_path(f"/data-product/{product_id}/")
        result = self.get(endpoint)
        if isinstance(result, dict):
            result["url"] = url_helper.data_product_url(product_id)
        return result

    def list_products(
        self, limit: int = 100, offset: int = 0, order_by: str = "-ts_updated"
    ) -> dict[str, Any]:
        """List all accessible data products.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            order_by: Sort order field (prefix with - for descending)

        Returns:
            Dict with 'results' containing simplified product entries.
        """
        endpoint = self._api_path("/data-product/")
        params = {"limit": limit, "skip": offset, "order_by": order_by}
        result = self.get(endpoint, params)

        # Simplify results to avoid ID confusion
        for item in result.get("results", []):
            item.pop("id", None)
            item.pop("tenant_id", None)

            spec = item.get("spec_json", {})
            product_info = spec.get("product", {}).get("en", {})
            if "name" not in item and product_info.get("name"):
                item["name"] = product_info["name"]
            if "description" not in item and product_info.get("description"):
                item["description"] = product_info["description"]

            if item.get("product_id"):
                item["url"] = url_helper.data_product_url(item["product_id"])

        return result

    # --- SQL Execution API (uses AI path prefix + tool chat endpoint) ---

    def _stream_tool_call(
        self, tool_ref: str, payload: dict[str, Any], timeout_secs: float = 120.0
    ) -> dict[str, Any]:
        """Invoke a tool via the streaming chat API and collect the result.

        Sends a POST to the tool stream endpoint, parses SSE events, and returns
        the tool-return content and metadata.

        Args:
            tool_ref: Tool reference name (e.g., "sql_execution_tool")
            payload: Tool parameters
            timeout_secs: Request timeout in seconds

        Returns:
            Dict with "content" and "metadata" from the tool-return event
        """
        if not self._opener:
            raise RuntimeError("Client not initialized. Use 'with' context manager.")

        endpoint = f"/api/v1/chats/tool/default/{tool_ref}/stream"
        result: dict[str, Any] = {"content": None, "metadata": None}
        text_parts: list[str] = []

        response = self._stream_request("POST", endpoint, json_data=payload, timeout=timeout_secs)
        for raw_bytes in response:
            line = raw_bytes.decode("utf-8").strip()
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict) or "model_message" not in event:
                continue
            for part in event["model_message"].get("parts", []):
                kind = part.get("part_kind", "")
                if kind in ("tool-return", "builtin-tool-return"):
                    result["content"] = part.get("content")
                    result["metadata"] = part.get("metadata")
                elif kind == "text" and part.get("content"):
                    text_parts.append(part["content"])
        # If there is no tool response, check for any text parts
        # in case there was an unrecoverable error.
        if result["content"] is None and text_parts:
            result["content"] = "\n".join(text_parts)

        return result

    def execute_sql(
        self,
        product_id: str,
        sql: str,
        result_table_name: str | None = None,
        auth_id: str | None = None,
        timeout_secs: float = 120.0,
        allow_fallback_auth: bool = True,
    ) -> dict[str, Any]:
        """Execute SQL query against a data product.

        Args:
            product_id: Data product to query
            sql: SQL query to execute
            result_table_name: Name for the result table (auto-generated if not provided)
            auth_id: Auth credentials ID for the data product
            timeout_secs: Request timeout in seconds
            allow_fallback_auth: Allow fallback to default credentials if no auth_id configured
        """
        if result_table_name is None:
            result_table_name = f"result_{uuid.uuid4().hex[:8]}"

        payload: dict[str, Any] = {
            "data_product_id": product_id,
            "sql": sql,
            "result_table_name": result_table_name,
        }
        if auth_id:
            payload["auth_id"] = auth_id
        if allow_fallback_auth:
            payload["allow_fallback_auth"] = True

        start_time = time.time()
        result = self._stream_tool_call(
            "sql_execution_tool", payload, timeout_secs=timeout_secs
        )
        elapsed = time.time() - start_time

        content = result.get("content")
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass

        return {
            "results": content,
            "metadata": result.get("metadata"),
            "execution_time_seconds": round(elapsed, 2),
            "product_id": product_id,
            "url": url_helper.data_product_url(product_id),
        }

    def execute_sql_async(
        self,
        product_id: str,
        sql: str,
        result_table_name: str | None = None,
        auth_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute SQL as a background task (for long-running queries).

        Args:
            product_id: Data product to query
            sql: SQL query to execute
            result_table_name: Name for the result table
            auth_id: Auth credentials ID for the data product
        """
        if not self._opener:
            raise RuntimeError("Client not initialized. Use 'with' context manager.")

        if result_table_name is None:
            result_table_name = f"result_{uuid.uuid4().hex[:8]}"

        endpoint = "/api/v1/chats/tool/default/sql_execution_tool/call"
        payload: dict[str, Any] = {
            "data_product_id": product_id,
            "sql": sql,
            "result_table_name": result_table_name,
        }
        if auth_id:
            payload["auth_id"] = auth_id

        return cast("dict[str, Any]", self.post(endpoint, payload))

    def validate_sql(self, product_id: str, sql: str) -> dict[str, Any] | None:
        """Validate SQL against data product schema without executing.

        Args:
            product_id: Data product to validate against
            sql: SQL query to validate
        """
        if not self._opener:
            raise RuntimeError("Client not initialized. Use 'with' context manager.")
        endpoint = f"/api/v2/data-product/{product_id}/validate-sql/"
        return self.post(endpoint, {"sql_statements": [sql]})


def _parse_database_from_uri(uri: str) -> str | None:
    """Extract database name from a delivery system URI."""
    match = re.search(r"[?&]db=([^&]+)", uri)
    return match.group(1) if match else None


def extract_schema_summary(product_data: dict[str, Any]) -> dict[str, Any]:
    """Extract a clean schema summary from product data for LLM consumption.

    Args:
        product_data: Raw product data from get_product()

    Returns:
        Simplified schema with product info, record sets, and columns.
    """
    spec = product_data.get("spec_json", {})
    product = spec.get("product", {})

    pid = product_data.get("product_id")
    summary: dict[str, Any] = {
        "product_id": pid,
        "url": url_helper.data_product_url(pid) if pid else None,
        "name": product.get("en", {}).get("name"),
        "description": product.get("en", {}).get("description"),
        "record_sets": [],
        "delivery_systems": [],
    }

    default_database: str | None = None
    for ds_key, ds_data in product.get("deliverySystems", {}).items():
        uri = ds_data.get("uri", "")
        database = _parse_database_from_uri(uri)
        if database and not default_database:
            default_database = database
        summary["delivery_systems"].append(
            {
                "key": ds_key,
                "type": ds_data.get("type"),
                "uri": uri,
                "database": database,
            }
        )

    product_id = product_data.get("product_id", "")
    product_id_upper = product_id.upper() if product_id else None

    for rs_key, rs_data in product.get("recordSets", {}).items():
        table_name = rs_data.get("name", rs_key)
        record_set: dict[str, Any] = {
            "key": rs_key,
            "name": table_name,
            "description": rs_data.get("description"),
            "columns": [],
        }

        if default_database and product_id_upper:
            record_set["qualified_name"] = (
                f"{default_database}.{product_id_upper}.{table_name.upper()}"
            )

        for col in rs_data.get("schema", []):
            record_set["columns"].append(
                {
                    "name": col.get("name"),
                    "type": col.get("type"),
                    "description": col.get("description"),
                }
            )
        summary["record_sets"].append(record_set)

    return summary

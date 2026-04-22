"""Client for BI object discovery — detail and cross-navigation."""

import json
import urllib.error
from typing import Any, cast

from .base import AlationClient, poll_tool_result
from . import url_helper

_MAX_COLUMNS = 500
# Looker tool calls can be slow due to large data volumes; 30s is intentional.
_LOOKER_POLL_ATTEMPTS = 30


class BiClient(AlationClient):

    def _direct_get(self, path: str, params: dict | None = None) -> Any:
        """GET against base_url directly, bypassing the AI gateway prefix."""
        resp = self._request(
            "GET", f"{self.base_url}{path}", headers=self._headers(), params=params,
        )
        body = resp.read().decode()
        return json.loads(body) if body else None

    # --- Detail ---

    def get_report(self, report_id: int) -> dict[str, Any]:
        """GET /api/v2/bi_report/{report_id}/ (direct Alation API, no AI prefix)."""
        result = self._direct_get(f"/api/v2/bi_report/{report_id}/")
        if isinstance(result, dict):
            result["url"] = url_helper.bi_report_url(report_id)
        return cast("dict[str, Any]", result)

    def get_datasource_views(self, datasource_id: int) -> dict[str, Any]:
        """Get semantic layer views for a BI datasource.

        Fetches semantic views from BI datasource (Looker Explore, Power BI dataset, etc).
        """
        try:
            result = self.get(f"/api/v1/bi/datasource/{datasource_id}/views")
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            # Looker handling is still done through the tool.
            # This can be removed when the looker implementation is migrated to the views endpoint.
            dialect = self._detect_dialect_from_connections(datasource_id)
            if not dialect:
                return {
                    "error": "Could not auto-detect the SQL dialect for this datasource. "
                    "The BI connection metadata did not contain a database_type."
                }
            result = self._process_bi_connection_tool(
                datasource_id, dialect, max_columns=_MAX_COLUMNS,
            )
        return cast("dict[str, Any]", result)

    def get_product_spec(self, datasource_id: int) -> str:
        """Get a data product spec (YAML) for a BI datasource semantic layer."""
        try:
            result = self.post(
                "/api/v1/data_product/create_from_bi_datasource",
                data=None,
                params={"datasource_id": datasource_id, "create_product": "false"},
            )
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            # Looker handling is still done through the tool.
            # This can be removed when the looker implementation is migrated to the endpoint.
            dialect = self._detect_dialect_from_connections(datasource_id)
            if not dialect:
                return (
                    "error: Could not auto-detect the SQL dialect for this datasource. "
                    "The BI connection metadata did not contain a database_type."
                )
            result = self._bi_explore_to_data_product_tool(datasource_id, dialect)
            if isinstance(result, dict):
                result = result.get("raw_content", "") or ""
        return cast("str", result or "")

    # --- Cross-navigation via lineage ---

    def report_datasources(self, report_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """Get datasources upstream of a report."""
        return self._lineage_query(
            oid=report_id, otype="bi_report",
            direction="upstream", target_otype="bi_datasource", limit=limit,
        )

    def datasource_reports(self, datasource_id: int, limit: int = 100) -> list[dict[str, Any]]:
        """Get reports downstream of a datasource."""
        return self._lineage_query(
            oid=datasource_id, otype="bi_datasource",
            direction="downstream", target_otype="bi_report", limit=limit,
        )

    def _lineage_query(
        self, oid: int, otype: str, direction: str, target_otype: str, limit: int,
    ) -> list[dict[str, Any]]:
        payload = {
            "key_type": "id",
            "root_nodes": [{"id": oid, "otype": otype}],
            "direction": direction,
            "filters": {"depth": 3},
            "limit": limit,
        }
        result = self.post("/integration/v2/bulk_lineage/", payload)
        graph = result.get("graph", []) if isinstance(result, dict) else []

        found: dict[int, dict[str, Any]] = {}
        for node in graph:
            if node.get("otype") == target_otype and node.get("id") not in found:
                found[node["id"]] = node
            for neighbor in node.get("neighbors", []):
                nid = neighbor.get("id")
                if neighbor.get("otype") == target_otype and nid not in found:
                    found[nid] = neighbor

        for node in found.values():
            node_id = node["id"]
            if target_otype == "bi_report":
                node["url"] = url_helper.bi_report_url(int(node_id))
            elif target_otype == "bi_datasource":
                node["url"] = url_helper.bi_datasource_url(int(node_id))
        return cast("list[dict[str, Any]]", list(found.values()))

    # --- Looker fallback (remove when views endpoint supports Looker) ---

    _CONNECTION_FIELDS = (
        "host", "port", "database_type", "db_schema", "db_table",
        "connection_type", "display_connection_type",
    )

    def _get_connections(self, datasource_id: int) -> list[dict[str, Any]]:
        """Get physical connection info for a BI datasource."""
        results = self._direct_get(
            "/api/v2/bi_connection/", {"data_source_id": datasource_id},
        )
        if not isinstance(results, list):
            results = [results] if isinstance(results, dict) else []
        return [
            {k: conn.get(k) for k in self._CONNECTION_FIELDS}
            for conn in results
        ]

    _DIALECT_MAP: dict[str, str] = {
        "bigquery_standard_sql": "bigquery",
        "bigquery_legacy_sql": "bigquery",
        "bigquery": "bigquery",
        "databricks": "databricks",
        "hana": "hana",
        "postgres": "postgres",
        "postgresql": "postgres",
        "redshift": "redshift",
        "snowflake": "snowflake",
        "teradata": "teradata",
        "trino": "trino",
        "tsql": "tsql",
        "mssql": "tsql",
        "sqlserver": "tsql",
    }

    def _detect_dialect_from_connections(self, datasource_id: int) -> str | None:
        try:
            connections = self._get_connections(datasource_id)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, KeyError):
            return None
        for conn in connections:
            db_type = conn.get("database_type")
            if db_type:
                return self._DIALECT_MAP.get(db_type.lower(), db_type.lower())
        return None

    def _bi_explore_to_data_product_tool(self, datasource_id: int, dialect: str) -> dict[str, Any]:
        """Async tool call to bi_explore_to_data_product, same poll pattern as SearchClient."""
        try:
            result = self.post(
                "/api/v1/chats/tool/default/bi_explore_to_data_product_tool/call",
                {"datasource_id": datasource_id, "dialect": dialect},
            )
        except urllib.error.HTTPError:
            return {"error": "bi_explore_to_data_product_tool call failed"}
        chat_id = result["chat_id"]
        return poll_tool_result(
            self, chat_id,
            max_attempts=_LOOKER_POLL_ATTEMPTS,
            default={"error": "bi_explore_to_data_product_tool timed out"},
        )

    def _process_bi_connection_tool(
        self, datasource_id: int, dialect: str, max_columns: int | None = None,
    ) -> dict[str, Any]:
        """Async tool call to process_bi_connection_tool, same poll pattern as SearchClient."""
        payload: dict[str, Any] = {"datasource_id": datasource_id, "dialect": dialect}
        if max_columns is not None:
            payload["max_columns"] = max_columns
        try:
            result = self.post(
                "/api/v1/chats/tool/default/process_bi_connection_tool/call",
                payload,
            )
        except urllib.error.HTTPError:
            return {"error": "process_bi_connection_tool call failed"}
        chat_id = result["chat_id"]
        return poll_tool_result(
            self, chat_id,
            max_attempts=_LOOKER_POLL_ATTEMPTS,
            default={"error": "process_bi_connection_tool timed out"},
        )


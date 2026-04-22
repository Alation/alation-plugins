"""Client for BI object discovery — detail and cross-navigation."""

import json
from typing import Any, cast

from .base import AlationClient
from . import url_helper


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
        result = self.get(f"/api/v1/bi/datasource/{datasource_id}/views")
        return cast("dict[str, Any]", result)

    def get_product_spec(self, datasource_id: int) -> str:
        """Get a data product spec (YAML) for a BI datasource semantic layer."""
        result = self.post(
            "/api/v1/data_product/create_from_bi_datasource",
            data=None,
            params={"datasource_id": datasource_id, "create_product": "false"},
        )
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

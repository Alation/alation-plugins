"""Client for data source administration.

Uses TOKEN auth for /integration/v2/ datasource endpoints.
"""

from typing import Any, cast

from .base import AlationClient
from . import url_helper

_API_BASE = "/integration/v2"


class AdminClient(AlationClient):
    """Client for administering Alation data sources.

    Usage:
        with AdminClient() as client:
            sources = client.list_datasources()
    """

    def _api_path(self, path: str) -> str:
        return f"{_API_BASE}{path}"

    def list_datasources(self, limit: int = 100, skip: int = 0) -> list[dict[str, Any]]:
        """List all data sources."""
        result = self.get(
            self._api_path("/datasource/"),
            {"limit": limit, "skip": skip},
        )
        for ds in result:
            ds["url"] = url_helper.datasource_url(ds["id"])
        return cast("list[dict[str, Any]]", result)

    def get_datasource(self, ds_id: int) -> dict[str, Any]:
        """Get a specific data source."""
        result = self.get(self._api_path(f"/datasource/{ds_id}"))
        result["url"] = url_helper.datasource_url(ds_id)
        return cast("dict[str, Any]", result)

    def create_datasource(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Create a new data source."""
        result = self.post(self._api_path("/datasource/"), spec)
        if isinstance(result, dict) and "id" in result:
            result["url"] = url_helper.datasource_url(result["id"])
        return result

    def update_datasource(self, ds_id: int, spec: dict[str, Any]) -> dict[str, Any]:
        """Update a data source."""
        result = self.put(self._api_path(f"/datasource/{ds_id}"), spec)
        if isinstance(result, dict):
            result["url"] = url_helper.datasource_url(ds_id)
        return result

    def delete_datasource(self, ds_id: int) -> None:
        """Delete a data source."""
        self.delete(self._api_path(f"/datasource/{ds_id}"))

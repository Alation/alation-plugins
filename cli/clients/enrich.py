"""Client for metadata enrichment.

Uses TOKEN auth for /integration/v2/ custom field endpoints.
"""

from typing import Any, cast

from .base import AlationClient

_API_BASE = "/integration/v2"


class EnrichClient(AlationClient):
    """Client for enriching catalog metadata.

    Usage:
        with EnrichClient() as client:
            fields = client.list_custom_fields()
    """

    def _api_path(self, path: str) -> str:
        return f"{_API_BASE}{path}"

    def list_custom_fields(self, limit: int = 100, skip: int = 0) -> list[dict[str, Any]]:
        """List all custom fields."""
        result = self.get(
            self._api_path("/custom_field/"),
            {"limit": limit, "skip": skip},
        )
        return cast("list[dict[str, Any]]", result)

    def get_custom_field(self, field_id: int) -> dict[str, Any]:
        """Get a specific custom field."""
        return self.get(self._api_path(f"/custom_field/{field_id}"))

    def get_field_values(
        self, otype: str, oid: int
    ) -> list[dict[str, Any]]:
        """Get custom field values for an object."""
        result = self.get(
            self._api_path("/custom_field_value/"),
            {"otype": otype, "oid": oid},
        )
        return cast("list[dict[str, Any]]", result)

    def set_field_value(
        self,
        otype: str,
        oid: int,
        field_id: int,
        value: Any,
    ) -> dict[str, Any]:
        """Set a custom field value for an object."""
        payload = [{
            "field_id": field_id,
            "otype": otype,
            "oid": oid,
            "value": value,
        }]
        return self.put(self._api_path("/custom_field_value/"), payload)

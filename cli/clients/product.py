"""Client for data product configuration management.

Extends AlationClient for the Data Products API (/integration/data-products/api/v1/).
"""

from typing import Any, cast

from .base import AlationClient
from . import url_helper

_API_BASE = "/integration/data-products/api/v1"


class DataProductConfigClient(AlationClient):
    """Client for the Alation Data Products Configuration API.

    Handles authentication automatically via the parent AlationClient.

    Usage:
        with DataProductConfigClient() as client:
            products = client.list_products()
    """

    def _api_path(self, path: str) -> str:
        """Build full API path."""
        return f"{_API_BASE}{path}"

    # --- Data Product CRUD ---

    def list_products(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "-ts_updated",
    ) -> list[dict[str, Any]]:
        """List data products."""
        params: dict[str, Any] = {
            "limit": limit,
            "skip": offset,
            "order_by": order_by,
        }
        result = self.get(self._api_path("/data-product/"), params)
        products = result.get("results", result if isinstance(result, list) else [])
        for product in products:
            pid = product.get("product_id") or product.get("id")
            if pid:
                product["url"] = url_helper.data_product_url(pid)
        return cast("list[dict[str, Any]]", products)

    def get_product(self, product_id: str) -> dict[str, Any]:
        """Get a specific data product."""
        result = self.get(self._api_path(f"/data-product/{product_id}/"))
        if isinstance(result, dict):
            result["url"] = url_helper.data_product_url(product_id)
        return cast("dict[str, Any]", result)

    def create_product(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Create a new data product from a spec JSON body."""
        result = self.post(self._api_path("/data-product/"), spec)
        if isinstance(result, dict):
            pid = result.get("product_id") or result.get("id")
            if pid:
                result["url"] = url_helper.data_product_url(pid)
        return cast("dict[str, Any]", result)

    def update_product(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Update a data product. The spec must contain the product_id."""
        result = self.put(self._api_path("/data-product/"), spec)
        if isinstance(result, dict):
            pid = result.get("product_id") or result.get("id")
            if pid:
                result["url"] = url_helper.data_product_url(pid)
        return cast("dict[str, Any]", result)

    def delete_product(self, product_id: str) -> None:
        """Delete a data product."""
        self.delete(self._api_path(f"/data-product/{product_id}/"))

    # --- Data Product Version Management ---

    def get_version(self, product_id: str, version_id: str) -> dict[str, Any]:
        """Get a specific version of a data product."""
        return cast(
            "dict[str, Any]",
            self.get(self._api_path(f"/data-product/{product_id}/version/{version_id}/")),
        )

    def update_version(self, product_id: str, version_id: str, status: str) -> dict[str, Any]:
        """Update a data product version status (draft or ready)."""
        return cast(
            "dict[str, Any]",
            self.put(
                self._api_path(f"/data-product/{product_id}/version/{version_id}/"),
                {"status": status},
            ),
        )

    def delete_version(self, product_id: str, version_id: str) -> None:
        """Delete a data product version."""
        self.delete(self._api_path(f"/data-product/{product_id}/version/{version_id}/"))

    # --- Standards Check ---

    def check_standards(
        self, product_spec: dict[str, Any], standards: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Check a data product spec against a set of standards."""
        payload = {"product_spec": product_spec, "standards": standards}
        return cast("list[dict[str, Any]]", self.post(self._api_path("/data-product-check/"), payload))

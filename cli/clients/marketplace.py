"""Client for marketplace management.

Extends AlationClient for the Data Marketplaces API, including
marketplace CRUD, product publishing, and search.
"""

from typing import Any, cast

from . import url_helper
from .base import AlationClient

_API_BASE = "/integration/data-products/api/v1"


class MarketplaceClient(AlationClient):
    """Client for the Data Marketplaces API.

    Handles authentication automatically via the parent AlationClient.

    Usage:
        with MarketplaceClient() as client:
            marketplaces = client.list_marketplaces()
    """

    def _api_path(self, path: str) -> str:
        """Build full API path."""
        return f"{_API_BASE}{path}"

    # --- Marketplace CRUD ---

    def list_marketplaces(
        self, limit: int = 100, skip: int = 0
    ) -> list[dict[str, Any]]:
        """List all data marketplaces."""
        endpoint = self._api_path("/marketplace/")
        params: dict[str, Any] = {"limit": limit, "skip": skip}
        result = self.get(endpoint, params)
        marketplaces = result.get("data", result if isinstance(result, list) else [])
        for mp in marketplaces:
            mid = mp.get("marketplace_id") or mp.get("id")
            if mid:
                mp["url"] = url_helper.marketplace_url(mid)
        return cast("list[dict[str, Any]]", marketplaces)

    def get_marketplace(self, marketplace_id: str) -> dict[str, Any]:
        """Get details of a specific marketplace."""
        endpoint = self._api_path(f"/marketplace/{marketplace_id}/")
        result = self.get(endpoint)
        if isinstance(result, dict):
            result["url"] = url_helper.marketplace_url(marketplace_id)
        return cast("dict[str, Any]", result)

    def create_marketplace(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Create a new marketplace."""
        endpoint = self._api_path("/marketplace/")
        result = self.post(endpoint, spec)
        if isinstance(result, dict):
            mid = result.get("marketplace_id") or result.get("id")
            if mid:
                result["url"] = url_helper.marketplace_url(mid)
        return cast("dict[str, Any]", result)

    def update_marketplace(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Update an existing marketplace."""
        endpoint = self._api_path("/marketplace/")
        result = self.put(endpoint, spec)
        if isinstance(result, dict):
            mid = result.get("marketplace_id") or result.get("id")
            if mid:
                result["url"] = url_helper.marketplace_url(mid)
        return cast("dict[str, Any]", result)

    def delete_marketplace(self, marketplace_id: str) -> None:
        """Delete a marketplace."""
        endpoint = self._api_path(f"/marketplace/{marketplace_id}/")
        self.delete(endpoint)

    # --- Products in Marketplace ---

    def list_products(
        self, marketplace_id: str, limit: int = 100, skip: int = 0
    ) -> list[dict[str, Any]]:
        """List data products published in a marketplace."""
        endpoint = self._api_path(f"/marketplace/{marketplace_id}/data-product/")
        params: dict[str, Any] = {"limit": limit, "skip": skip}
        products = self.get(endpoint, params)
        for product in products:
            pid = product.get("product_id") or product.get("id")
            if pid:
                product["url"] = url_helper.data_product_url(pid)
        return cast("list[dict[str, Any]]", products)

    def publish_product(
        self, marketplace_id: str, product_id: str, version: str | None = None
    ) -> dict[str, Any]:
        """Publish a data product to a marketplace."""
        endpoint = self._api_path(
            f"/marketplace/{marketplace_id}/data-product/{product_id}/"
        )
        params = {"version": version} if version else None
        result = self.post(endpoint, params=params)
        if isinstance(result, dict):
            result["marketplace_url"] = url_helper.marketplace_url(marketplace_id)
            result["product_url"] = url_helper.data_product_url(product_id)
        return cast("dict[str, Any]", result)

    def unpublish_product(self, marketplace_id: str, product_id: str) -> None:
        """Unpublish a data product from a marketplace."""
        endpoint = self._api_path(
            f"/marketplace/{marketplace_id}/data-product/{product_id}/"
        )
        self.delete(endpoint)

    # --- Search ---

    def search_products(self, marketplace_id: str, query: str) -> list[dict[str, Any]]:
        """Search for data products within a marketplace using natural language."""
        endpoint = self._api_path(f"/search-internally/{marketplace_id}/")
        result = self.post(endpoint, {"user_query": query})
        if isinstance(result, list):
            for product in result:
                pid = product.get("product_id") or product.get("id")
                if pid:
                    product["url"] = url_helper.data_product_url(pid)
        return cast("list[dict[str, Any]]", result)

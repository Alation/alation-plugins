"""Client for schema exploration.

Extends AlationClient for browsing data source hierarchies:
datasources -> schemas -> tables -> columns.
"""

from typing import Any, cast

from .base import AlationClient
from . import url_helper

_API_BASE = "/integration/v2"


class BrowseClient(AlationClient):
    """Client for browsing Alation data source hierarchies.

    Uses TOKEN auth automatically for /integration/v2/ endpoints.

    Usage:
        with BrowseClient() as client:
            sources = client.list_datasources()
    """

    def _api_path(self, path: str) -> str:
        """Build full API path."""
        return f"{_API_BASE}{path}"

    # --- Datasources ---

    def list_datasources(self, limit: int = 100, skip: int = 0) -> list[dict[str, Any]]:
        """List all data sources."""
        result = self.get(self._api_path("/datasource/"), {"limit": limit, "skip": skip})
        for ds in result:
            ds["url"] = url_helper.datasource_url(ds["id"])
        return cast("list[dict[str, Any]]", result)

    def get_datasource(self, ds_id: int) -> dict[str, Any]:
        """Get a specific data source."""
        result = self.get(self._api_path(f"/datasource/{ds_id}"))
        result["url"] = url_helper.datasource_url(ds_id)
        return cast("dict[str, Any]", result)

    # --- Schemas ---

    def list_schemas(
        self, ds_id: int, limit: int = 100, skip: int = 0
    ) -> list[dict[str, Any]]:
        """List schemas in a data source."""
        result = self.get(
            self._api_path("/schema/"), {"ds_id": ds_id, "limit": limit, "skip": skip}
        )
        for schema in result:
            schema["url"] = url_helper.schema_url(schema["id"])
        return cast("list[dict[str, Any]]", result)

    def get_schema(self, schema_id: int) -> dict[str, Any]:
        """Get a specific schema."""
        results = self.get(self._api_path("/schema/"), {"id": schema_id})
        if not results:
            raise ValueError(f"Schema {schema_id} not found")
        result = results[0]
        result["url"] = url_helper.schema_url(schema_id)
        return cast("dict[str, Any]", result)

    # --- Tables ---

    def list_tables(
        self,
        ds_id: int | None = None,
        schema_id: int | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """List tables in a schema or data source."""
        params: dict[str, Any] = {"limit": limit, "skip": skip}
        if schema_id is not None:
            params["schema_id"] = schema_id
        elif ds_id is not None:
            params["ds_id"] = ds_id
        else:
            raise ValueError("Must specify either ds_id or schema_id")

        result = self.get(self._api_path("/table/"), params)
        for table in result:
            table["url"] = url_helper.table_url(table["id"])
        return cast("list[dict[str, Any]]", result)

    def get_table(self, table_id: int) -> dict[str, Any]:
        """Get a specific table."""
        results = self.get(self._api_path("/table/"), {"id": table_id})
        if not results:
            raise ValueError(f"Table {table_id} not found")
        result = results[0]
        result["url"] = url_helper.table_url(table_id)
        return cast("dict[str, Any]", result)

    # --- Columns ---

    def list_columns(
        self,
        table_id: int | None = None,
        ds_id: int | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """List columns in a table or data source."""
        params: dict[str, Any] = {"limit": limit, "skip": skip}
        if table_id is not None:
            params["table_id"] = table_id
        elif ds_id is not None:
            params["ds_id"] = ds_id
        else:
            raise ValueError("Must specify either table_id or ds_id")

        result = self.get(self._api_path("/column/"), params)
        for col in result:
            col["url"] = url_helper.column_url(col["id"])
        return cast("list[dict[str, Any]]", result)

    def get_column(self, column_id: int) -> dict[str, Any]:
        """Get a specific column."""
        results = self.get(self._api_path("/column/"), {"id": column_id})
        if not results:
            raise ValueError(f"Column {column_id} not found")
        result = results[0]
        result["url"] = url_helper.column_url(column_id)
        return cast("dict[str, Any]", result)

    # --- Tree View ---

    def get_tree(self, ds_id: int, depth: int = 2) -> dict[str, Any]:
        """Get hierarchical view of a data source.

        Args:
            ds_id: Data source ID
            depth: 1=schemas only, 2=schemas+tables, 3=schemas+tables+columns

        Returns:
            Nested dict with datasource -> schemas -> tables -> columns
        """
        ds = self.get_datasource(ds_id)
        tree: dict[str, Any] = {
            "id": ds["id"],
            "title": ds.get("title"),
            "dbtype": ds.get("dbtype"),
            "url": ds.get("url"),
            "schemas": [],
        }

        if depth < 1:
            return tree

        schemas = self.list_schemas(ds_id, limit=500)
        for schema in schemas:
            schema_node: dict[str, Any] = {
                "id": schema["id"],
                "name": schema.get("name"),
                "url": schema.get("url"),
                "tables": [],
            }

            if depth >= 2:
                tables = self.list_tables(schema_id=schema["id"], limit=500)
                for table in tables:
                    table_node: dict[str, Any] = {
                        "id": table["id"],
                        "name": table.get("name"),
                        "url": table.get("url"),
                        "columns": [],
                    }

                    if depth >= 3:
                        columns = self.list_columns(table_id=table["id"], limit=500)
                        for col in columns:
                            table_node["columns"].append({
                                "id": col["id"],
                                "name": col.get("name"),
                                "column_type": col.get("column_type"),
                                "url": col.get("url"),
                            })

                    schema_node["tables"].append(table_node)

            tree["schemas"].append(schema_node)

        return tree

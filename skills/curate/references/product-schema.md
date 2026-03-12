# Data Product Spec JSON Schema

The data product API accepts a `SpecJson` object. The top-level key is `product`.

## Verified Working Example

This example demonstrates the correct format that works with the API:

```json
{
  "product": {
    "productId": "my-data-product",
    "version": "1.0.0",
    "contactEmail": "data-team@example.com",
    "contactName": "Data Team",
    "en": {
      "name": "My Data Product",
      "description": "Description of what this data product contains."
    },
    "deliverySystems": {
      "snowflake": {
        "type": "sql",
        "uri": "snowflake://myaccount.snowflakecomputing.com:443/?warehouse=COMPUTE_WH"
      }
    },
    "recordSets": {
      "my_table": {
        "name": "my_table",
        "description": "Description of what each row represents",
        "schema": [],
        "dataAccess": [
          {
            "type": "SQL",
            "qualifiedName": {
              "database": "MY_DATABASE",
              "schema": "MY_SCHEMA",
              "table": "MY_TABLE"
            }
          }
        ]
      }
    }
  }
}
```

**Important notes:**
- `deliverySystems.<name>.type` must be **lowercase** (`"sql"`, not `"SQL"`)
- `dataAccess[].type` is **uppercase** (`"SQL"`)
- `dataAccess` only requires `type` and `qualifiedName` - other fields like `host`, `format`, `documentationUrl` are not needed
- Use `"schema": []` when you don't know the exact column names yet

## SpecJson Schema Reference

```json
{
  "product": {
    "productId": "string (required, namespaced e.g. 'finance:sales')",
    "version": "string (required, semantic version e.g. '1.0.0')",
    "contactEmail": "string (required)",
    "contactName": "string (required)",
    "en": {
      "name": "string (required)",
      "description": "string",
      "shortDescription": "string",
      "logoUrl": "string (URL)"
    },
    "deliverySystems": {
      "<system_name>": {
        "type": "string (MUST be lowercase: 'sql')",
        "uri": "string (connection URI - must match catalog exactly)",
        "accessRequestInstruction": {
          "type": "manual",
          "instruction": "string",
          "request": "string (URL)"
        }
      }
    },
    "recordSets": {
      "<record_set_name>": {
        "name": "string",
        "description": "string",
        "schema": [
          {
            "name": "string (column name)",
            "description": "string",
            "type": "string (text, numeric, date, boolean, unknown)"
          }
        ],
        "dataAccess": [
          {
            "type": "SQL",
            "qualifiedName": {
              "database": "string",
              "schema": "string",
              "table": "string"
            }
          }
        ]
      }
    }
  }
}
```

## Field Details

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `productId` | string | Namespaced unique identifier (e.g., `finance:quarterly_sales`) |
| `version` | string | Semantic version string (e.g., `1.0.0`) |
| `contactEmail` | string | Email of the data product owner |
| `contactName` | string | Name of the data product owner |
| `en.name` | string | Display name of the data product |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `en.description` | string | Full description of what the data product contains |
| `en.shortDescription` | string | Brief summary shown in listings |
| `en.logoUrl` | string | URL to a logo/icon for the product |
| `deliverySystems` | object | Map of system name to connection details |
| `recordSets` | object | Map of record set name to schema and sample data |

### Delivery Systems

Each delivery system describes where the data lives:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Connection type - **must be lowercase** (e.g., `sql`, not `SQL`) |
| `uri` | string | Connection URI - **must exactly match** the catalog's `ocf_configuration.uri` |
| `accessRequestInstruction` | object | How to request access (optional) |

**Common mistake:** Using uppercase `"SQL"` for the type will cause a 400 error. Always use lowercase `"sql"`.

### Record Sets

Each record set describes a dataset within the product:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name |
| `description` | string | What each row represents |
| `schema` | array | Column definitions with `name`, `description`, `type` |
| `sample` | object | Sample data (`type: mock`, `data: CSV string`) |
| `dataAccess` | array | How to access the underlying data |

### Schema Behavior

The `schema` array in a recordSet affects how queries are executed and validated:

| Schema State | Behavior |
|--------------|----------|
| Empty array `[]` | Queries run directly against the table without column validation. Use this for initial discovery when column names are unknown. |
| Populated array | The system validates queries against defined columns. Incorrect column names will cause SQL compilation errors (e.g., "invalid identifier") - even for `SELECT *` queries. |

**Recommended workflow for unknown tables:**
1. Create the data product with `"schema": []`
2. Query with `SELECT * FROM <table> LIMIT 1` to discover actual column names
3. Update the data product with the correct schema based on query results

## Response Schema (DataProduct)

When reading a product, the response includes additional metadata:

```json
{
  "product_id": "string",
  "version_id": "string",
  "status": "draft|ready",
  "spec_json": { "product": { ... } },
  "spec_yaml": "string (YAML representation)",
  "ts_created": "datetime",
  "ts_updated": "datetime"
}
```

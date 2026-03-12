# Tool Invocation Workflow

Detailed workflow for directly invoking Alation AI tools via `python -m cli tool`.

## When to Use Direct Tool Invocation

Use tool invocation when:
- User knows exactly which tool to run and provides exact parameters
- User wants raw tool output without explanation or reasoning
- Single execution with no follow-up or iteration expected
- User says "just run X" or "execute this query" (no help needed)

## Step 1: Discover Available Tools

Default tools:
```bash
python -m cli tool list
```
See `configure/references/default-tools.md` for common default tools, or run `python -m cli tool list` to fetch the full list from the server.

Custom tools:
```bash
python -m cli tool list
```
Use the tool's `id` field (UUID) wherever you would use a default tool ref.

## Step 2: Check Tool Schema

```bash
# Default tool
python -m cli tool schema <tool_ref>

# Custom tool
python -m cli tool schema <tool_config_id>
```

This fetches the tool's parameter schema from the server.

## Step 3: Invoke the Tool

### Streaming (default)
```bash
# Default tool (by ref name)
echo '{"search_term": "sales tables"}' | python -m cli tool call search_catalog_tool

# Custom tool (by UUID)
echo '{"param": "value"}' | python -m cli tool call <tool_config_id>
```

### With Existing Chat ID
```bash
echo '{"search_term": "sales"}' | python -m cli tool call search_catalog_tool --chat-id <uuid>
```

### Async (for long-running operations)
```bash
echo '{"search_term": "sales"}' | python -m cli tool call-async search_catalog_tool
```

## Tool Intent Matching

| User Intent | Tool | Key Parameters |
|-------------|------|----------------|
| "search for tables", "find data" | `search_catalog_tool` | search_term |
| "show schema", "table structure" | `get_data_schema_tool` | data_product_id |
| "make chart", "visualize" | `generate_chart_tool` | chart_type, data |
| "get object details" | `get_catalog_object_tool` | object_type, object_id |
| "list data products" | `list_data_products_tool` | - |
| "run evaluation" | `sql_evaluation_tool` | eval_set_id |

## Search Disambiguation

The `search_catalog_tool` finds **tables, columns, BI reports, and other catalog objects** by keyword in the Alation catalog. For finding data products or browsing products in a marketplace, use the **explore** skill.

## Error Handling

See `error-codes.md` for the complete error code reference. Common codes:

- **10001**: Auth ID not provided for data product query
- **10003**: Credentials not found for auth ID
- **20001**: Context validation error
- **20002**: Access denied to catalog resources
- **30002**: Data product not found

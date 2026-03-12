# Default Tools Reference

These are commonly used system-provided tools. This is not an exhaustive list — to see all
available tools (including custom tools), run:

```bash
python -m cli tool list
```

## Key Tools

| Tool | Reference | Description |
|------|-----------|-------------|
| SQL Execution | `sql_execution_tool` | Execute SQL queries against data products |
| Get Data Schema | `get_data_schema_tool` | Retrieve schema information for data products |
| Search Catalog | `search_catalog_tool` | Search the data catalog |
| Get Context by ID | `get_context_by_id_tool` | Retrieve context for specific catalog objects |
| Generate Chart | `generate_chart_tool` | Create visualizations from data |
| List Data Products | `list_data_products_tool` | List available data products |
| Get Data Product Spec | `get_data_product_spec_tool` | Get data product specification |
| Get Catalog Object | `get_catalog_object_tool` | Retrieve catalog object details |
| Update Catalog Object | `update_catalog_object_tool` | Modify catalog object metadata |
| Lineage | `lineage_tool` | Query data lineage |
| BI Report Search | `bi_report_search_tool` | Search BI reports |

## Tool Selection Matrix for Agents

Use this when deciding which tools to assign to a new agent.

| Agent Purpose | Essential Tools | Optional Tools |
|---------------|-----------------|----------------|
| SQL Queries | sql_execution, get_data_schema | sql_evaluation |
| Catalog Search | search_catalog, get_context_by_id | bulk_retrieval, alation_context |
| Data Visualization | generate_chart | sql_execution, get_data_schema |
| Data Products | list_data_products, get_data_product_spec | sql_execution, update_data_product |
| Metadata Curation | get_catalog_object, update_catalog_object | get_custom_fields_definitions |
| Research | search_catalog, bulk_retrieval, get_context_by_id | lineage, get_data_quality |

### Recommended Combinations

- **SQL Agent:** `sql_execution_tool` + `get_data_schema_tool`
- **Query Validator:** `sql_execution_tool` + `sql_evaluation_tool`
- **Catalog Search:** `search_catalog_tool` + `get_context_by_id_tool`
- **Deep Research:** `search_catalog_tool` + `bulk_retrieval_tool` + `get_context_by_id_tool`
- **Charting Agent:** `generate_chart_tool` + `sql_execution_tool` + `get_data_schema_tool`
- **Curation:** `get_catalog_object_tool` + `update_catalog_object_tool` + `get_custom_fields_definitions_tool`

### Tool Limits

- **Simple agents:** 2-4 tools
- **Standard agents:** 4-6 tools
- **Complex/research agents:** 6-10 tools

More tools = more prompt tokens and harder for LLM to choose correctly. Only include tools the agent actually needs.

### Getting Tool IDs

```bash
# List all tools (default and custom)
python -m cli tool list

# Filter for specific tool
python -m cli tool list | jq '.[] | select(.function_name == "sql_execution_tool")'
```

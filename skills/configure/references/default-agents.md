# Default Agents Reference

These are commonly used system-provided agents. This is not an exhaustive list — to see all
available agents (including custom agents), run:

```bash
python -m cli agent list
```

Default agents can be used directly or cloned to create custom variations.

## Available Default Agents

### SQL Query Agent (`sql_query_agent`)

**Purpose:** Write and execute SQL queries against data products.

**Tools:**
- `sql_execution_tool` - Execute SQL queries
- `get_data_schema_tool` - Retrieve schema information

**Input Schema:**
```json
{
  "message": "User's question",
  "data_product_id": "Data product to query",
  "data_product_version": "Optional version"
}
```

**Best For:** Direct database queries, data extraction, analytics questions.

---

### Catalog Search Agent (`catalog_search_agent`)

**Purpose:** Search and explore the data catalog.

**Tools:**
- `search_catalog_tool` - Search catalog objects
- `get_context_by_id_tool` - Get detailed context

**Input Schema:**
```json
{
  "message": "Search query or question"
}
```

**Best For:** Finding tables, columns, data assets, understanding data landscape.

---

### Charting Agent (`charting_agent`)

**Purpose:** Create data visualizations and charts.

**Tools:**
- `generate_chart_tool` - Create visualizations
- `generate_chart_from_sql_and_code_tool` - Charts from SQL results

**Input Schema:**
```json
{
  "message": "What to visualize"
}
```

**Best For:** Creating bar charts, line graphs, pie charts from data.

---

### Deep Research Agent (`deep_research_agent`)

**Purpose:** Multi-step research and comprehensive analysis.

**Tools:** Multiple search, retrieval, and analysis tools.

**Input Schema:**
```json
{
  "message": "Research question or topic"
}
```

**Output:** Structured research plan with summary.

**Best For:** Complex questions requiring multiple data sources, thorough analysis.

---

### Data Product Query Agent (`data_product_query_agent`)

**Purpose:** Query data products with automatic product discovery.

**Tools:**
- `list_data_products_tool` - Find available data products
- `get_data_product_spec_tool` - Get specifications
- `sql_execution_tool` - Execute queries

**Input Schema:**
```json
{
  "message": "Query or question",
  "data_product_id": "Data product ID",
  "auth_id": "Optional auth credentials ID"
}
```

**Best For:** Querying when data product context is important.

---

### BI Report Agent (`bi_report_agent`)

**Purpose:** Search and explore BI reports.

**Tools:**
- `bi_report_search_tool` - Search BI reports

**Input Schema:**
```json
{
  "message": "What report to find"
}
```

**Best For:** Finding dashboards, reports, BI artifacts.

---

### Query Flow Agent (`query_flow_agent`)

**Purpose:** Orchestrate multi-agent query workflows.

**Tools:** Multiple agent-as-tool configurations.

**Input Schema:**
```json
{
  "message": "Complex query",
  "marketplace_id": "Optional marketplace filter"
}
```

**Best For:** Complex queries that need multiple specialized agents.

---

### Curation Agent (`curation_agent`)

**Purpose:** Curate and manage catalog content.

**Tools:** Catalog management and update tools.

**Input Schema:**
```json
{
  "message": "Curation request",
  "asset_ids": ["Optional", "list", "of", "assets"]
}
```

**Best For:** Updating metadata, descriptions, tags on catalog objects.

---

### Alamigo Agent (`alamigo_agent`)

**Purpose:** General help with the Alation product itself (not for data queries).

**Tools:** Broad set of Alation-specific tools.

**Input Schema:**
```json
{
  "message": "Any Alation-related question"
}
```

**Best For:** "How do I use X?" questions about the Alation product. Not suited for data queries — use other agents for that.

---

### Catalog Context Search Agent (`catalog_context_search_agent`)

**Purpose:** Search catalog with rich context retrieval.

**Tools:**
- `search_catalog_tool`
- `get_context_by_id_tool`
- `alation_context_tool`

**Input Schema:**
```json
{
  "message": "Search query with context needs"
}
```

**Best For:** When you need detailed context about found objects.

---

### Revise Data Product Agent (`revise_data_product_agent`)

**Purpose:** Improve and revise data products based on evaluation.

**Tools:** Data product management and evaluation tools.

**Input Schema:**
```json
{
  "message": "Revision request",
  "data_product_id": "Product to revise",
  "data_product_version": "Optional version"
}
```

**Best For:** Iteratively improving data product quality.

## Using Default Agents

### Get Default Agent Details

```bash
python -m cli agent get-default sql_query_agent
```

### Clone for Customization

```bash
# Get the ID first
python -m cli agent get-default catalog_search_agent

# Clone it
python -m cli agent clone <agent-id>

# Customize the clone
echo '{"name": "My Custom Search", "prompt": "..."}' | \
  python -m cli agent update <new-id>
```

### Selecting the Right Agent

This is a quick reference for common use cases. There may be other default or custom agents
better suited to your task — run `python -m cli agent list` to see everything available.

| Need | Agent |
|------|-------|
| SQL queries | `sql_query_agent` |
| Find data | `catalog_search_agent` |
| Visualizations | `charting_agent` |
| Deep analysis | `deep_research_agent` |
| Data products | `data_product_query_agent` |
| BI reports | `bi_report_agent` |
| Catalog updates | `curation_agent` |
| Product help (not data) | `alamigo_agent` |

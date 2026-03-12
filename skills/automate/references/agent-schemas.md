# Agent and Tool Schemas for Workflows

This document describes how to wire agents and tools into workflow nodes — both default and custom.

## Common Patterns

### Agent Output Keys

All agents produce output with the key `__agent_output__`. When referencing agent output in subsequent workflow nodes, use:

```json
{
  "type": "reference",
  "node_id": "<agent_node_id>",
  "output_key": "__agent_output__"
}
```

### Tool Output Keys

Tools produce output with the key `__tool_output__`. When referencing tool output:

```json
{
  "type": "reference",
  "node_id": "<tool_node_id>",
  "output_key": "__tool_output__"
}
```

---

## Default Agents

These are examples of commonly used default agents in workflows. There are other default and custom agents available — run `python -m cli agent list` to see all of them.

### data_product_query_agent

Queries data products using natural language.

**Input Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | The query to execute (natural language) |
| `data_product_id` | string | Yes | ID of the data product to query |
| `auth_id` | string | No | Authentication credentials ID |

**Example workflow node:**

```json
{
  "id": "query_data",
  "type": "type_agent",
  "data": {
    "inputs": {
      "message": {
        "type": "static",
        "value": "Show me total sales by region"
      },
      "data_product_id": {
        "type": "static",
        "value": "superstore"
      }
    },
    "config": {
      "agent_id": "a0af811d-5010-4e59-944f-2f9bb4594260",
      "description": "Query sales data"
    }
  }
}
```

**Output:** `__agent_output__` contains the query results as formatted text.

---

### sql_query_agent

Executes SQL queries with natural language understanding.

**Input Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | The query request |

**Example workflow node:**

```json
{
  "id": "run_query",
  "type": "type_agent",
  "data": {
    "inputs": {
      "message": {
        "type": "static",
        "value": "What are the top 10 customers by revenue?"
      }
    },
    "config": {
      "agent_id": "30ba2c31-a1b2-4c3d-8e5f-6a7b8c9d0e1f",
      "description": "Run SQL query"
    }
  }
}
```

---

### catalog_search_agent

Searches the Alation catalog.

**Input Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | Search query |

---

### charting_agent

Generates charts from data.

**Input Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | Chart request with data context |

---

## Custom Agents

Custom agents work in workflows exactly like default agents — set `agent_id` in the node config to the custom agent's UUID. The difference is that you must look up the agent's input schema from the server since it varies per agent.

### Step 1: Find the agent's UUID and input schema

Use the **configure** skill's agent scripts (not part of this skill):
```bash
# List all agents (default and custom)
python -m cli agent list

# Get a specific custom agent's config
python -m cli agent get <agent_uuid>
```

The response includes an `input_json_schema` field that describes exactly what inputs the agent expects. Use this to build the `inputs` section of the workflow node.

### Step 2: Build the workflow node

Map each field from `input_json_schema` to a workflow input entry. Each input is either:
- `"type": "static"` with a `"value"` — hardcoded value
- `"type": "reference"` with `"node_id"` and `"output_key"` — output from a previous node

**Example:** A custom agent that expects `message` and `project_name`:

```json
{
  "id": "run_custom_agent",
  "type": "type_agent",
  "data": {
    "inputs": {
      "message": {
        "type": "static",
        "value": "Generate the weekly summary"
      },
      "project_name": {
        "type": "static",
        "value": "Project Alpha"
      }
    },
    "config": {
      "agent_id": "e4f7a1b2-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
      "description": "Run custom agent"
    }
  }
}
```

**Output:** Custom agents produce `__agent_output__` just like default agents. You can reference this output in subsequent nodes the same way.

---

## Default Tools

### SMTP Tools (e.g., smtp_html)

Send emails via SMTP.

**Input Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string or array | Yes | Recipient email(s) |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Email body content |
| `body_format` | string | No | "plain" or "html" (default: "plain") |
| `attachment_asset_ids` | array | No | Asset IDs to attach |

**Example workflow node:**

```json
{
  "id": "send_email",
  "type": "type_tool",
  "data": {
    "inputs": {
      "to": {
        "type": "static",
        "value": "user@example.com"
      },
      "subject": {
        "type": "static",
        "value": "Weekly Report"
      },
      "body": {
        "type": "reference",
        "node_id": "query_data",
        "output_key": "__agent_output__"
      },
      "body_format": {
        "type": "static",
        "value": "html"
      }
    },
    "config": {
      "tool_id": "4d580949-3c71-489d-ab40-5df0b2e96157",
      "description": "Send report email"
    }
  }
}
```

---

## Finding Agent/Tool IDs

Use the CLI to find IDs:

Use the **configure** skill's scripts (not part of this skill):
```bash
# List agents with their IDs and refs
python -m cli agent list

# Get default agent by reference
python -m cli agent get-default data_product_query_agent

# List tools
python -m cli tool list
```

## Common Agent References

| Agent | Default Ref | Typical Use |
|-------|-------------|-------------|
| Data Product Query | `data_product_query_agent` | Query data products |
| SQL Query | `sql_query_agent` | Run SQL queries |
| Catalog Search | `catalog_search_agent` | Search catalog |
| Chart Generation | `charting_agent` | Create visualizations |
| Curation | `curation_agent` | Curate catalog objects |

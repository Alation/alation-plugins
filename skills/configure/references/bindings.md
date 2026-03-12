# Parameter Bindings Guide

Parameter bindings control how tool parameters get their values at runtime.

## Binding Sources

| Source | Description | When to Use |
|--------|-------------|-------------|
| `fixed` | Hardcoded value in config | Value never changes (e.g., specific data product) |
| `user` | From agent's input payload | User provides value at runtime |
| `agent` | LLM decides the value | LLM should determine based on context |

## Binding Structure

```json
{
  "parameter_bindings": [
    {
      "param_name": {
        "source": "fixed|user|agent",
        "fixed_value": "value",  // only for source=fixed
        "payload_key": "key"     // optional, for source=user
      }
    }
  ]
}
```

**Important:** The array length must match `tool_config_ids` length.

## Common Patterns

### Pattern 1: Fixed Data Product

Lock an agent to a specific data product:

```json
{
  "tool_config_ids": ["<sql-execution-tool-id>"],
  "parameter_bindings": [
    {
      "data_product_id": {
        "source": "fixed",
        "fixed_value": "dp-sales-12345"
      }
    }
  ]
}
```

**Use case:** Agent dedicated to a single data product.

### Pattern 2: User-Provided Data Product

Let users specify the data product:

```json
{
  "tool_config_ids": ["<sql-execution-tool-id>"],
  "parameter_bindings": [
    {
      "data_product_id": {
        "source": "user"
      }
    }
  ],
  "input_json_schema": {
    "type": "object",
    "properties": {
      "message": {"type": "string"},
      "data_product_id": {"type": "string"}
    },
    "required": ["message", "data_product_id"]
  }
}
```

**Use case:** Flexible agent that works with any data product.

### Pattern 3: LLM-Decided Parameters

Let the LLM determine query limits, filters, etc.:

```json
{
  "tool_config_ids": ["<search-tool-id>"],
  "parameter_bindings": [
    {
      "query": {
        "source": "agent"
      },
      "limit": {
        "source": "agent"
      },
      "filters": {
        "source": "agent"
      }
    }
  ]
}
```

**Use case:** Search agents where LLM constructs the query.

### Pattern 4: Mixed Bindings

Combine fixed, user, and agent sources:

```json
{
  "tool_config_ids": ["<sql-execution-tool-id>", "<get-schema-tool-id>"],
  "parameter_bindings": [
    {
      "data_product_id": {
        "source": "fixed",
        "fixed_value": "dp-12345"
      },
      "timeout": {
        "source": "fixed",
        "fixed_value": 30
      }
    },
    {
      "data_product_id": {
        "source": "fixed",
        "fixed_value": "dp-12345"
      }
    }
  ]
}
```

**Use case:** Agent with some locked parameters and some flexible ones.

### Pattern 5: Payload Key Mapping

Map differently-named input fields:

```json
{
  "parameter_bindings": [
    {
      "data_product_id": {
        "source": "user",
        "payload_key": "product_id"
      }
    }
  ],
  "input_json_schema": {
    "type": "object",
    "properties": {
      "message": {"type": "string"},
      "product_id": {"type": "string"}
    },
    "required": ["message", "product_id"]
  }
}
```

**Use case:** When input field names don't match tool parameter names.

## Automatic Schema Generation

When using `source: "user"`, the parameter is automatically added to the agent's `input_json_schema` if not already present.

Example: If you have this binding:
```json
{
  "data_product_id": {
    "source": "user"
  }
}
```

The system will add `data_product_id` to the input schema with annotations showing which tool it's bound to.

## Multiple Tools with Same Parameter

When multiple tools need the same parameter (e.g., `data_product_id`), bind them consistently:

```json
{
  "tool_config_ids": ["<tool-1-id>", "<tool-2-id>"],
  "parameter_bindings": [
    {
      "data_product_id": {"source": "fixed", "fixed_value": "dp-123"}
    },
    {
      "data_product_id": {"source": "fixed", "fixed_value": "dp-123"}
    }
  ]
}
```

## Hidden Parameters

Some parameters are hidden from the LLM but still need bindings. These are marked with `x-hidden-from-model: true` in the tool's parameter schema.

Hidden parameters:
- Must have `source: "fixed"` or `source: "user"`
- Cannot be `source: "agent"` (LLM can't set hidden params)

## Validation Rules

1. **Array Length:** `parameter_bindings` length must equal `tool_config_ids` length
2. **Fixed Value Required:** When `source: "fixed"`, `fixed_value` must be provided
3. **Type Compatibility:** Fixed values must match the parameter's expected type
4. **Required Parameters:** Path parameters and required fields must have bindings

## Debugging Bindings

Check the effective input schema after creation:

```bash
python -m cli agent get <id> | jq '.input_json_schema'
```

The schema will show:
- `x-tool-bindings`: Which tools use this parameter
- `x-original-agent-input`: Parameters from original schema (not auto-added)

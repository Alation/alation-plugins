# LLM Reference

## Quick Selection Guide

| Use Case | Recommended LLM | Notes |
|----------|-----------------|-------|
| General purpose | `openai:gpt-5-2025-08-07` | Best overall performance |
| Fast responses | `openai:gpt-4o` | Lower latency, cost-effective |
| Complex reasoning | `openai:o3` | For analytical/planning tasks |
| EU data residency | Bedrock EU region | Data stays in EU |
| Cost optimization | `openai:gpt-4o` or Bedrock with caching | Balance of cost and quality |

## LLM Capabilities by Task

### SQL Query Agents

**Recommended:** GPT-5 or GPT-4o

- Strong SQL understanding
- Good at schema interpretation
- Handles complex joins and aggregations

### Search Agents

**Recommended:** GPT-5 or GPT-4o

- Good at query understanding
- Effective at result filtering
- Fast response for search operations

### Research/Analysis Agents

**Recommended:** O3 with high reasoning_effort

- Extended thinking for complex analysis
- Better at multi-step reasoning
- Handles ambiguous questions well

### Chart/Visualization Agents

**Recommended:** GPT-4o

- Fast for interactive chart creation
- Good at understanding visualization intent
- Cost-effective for repeated use

---

## Default LLM Configurations

These are the system-provided LLM configurations available out of the box. They are read-only but can be used directly by agents.

### OpenAI Models

| Name | Reference | Provider | Best For |
|------|-----------|----------|----------|
| GPT-5 | `openai:gpt-5-2025-08-07` | openai | General purpose, best overall |
| GPT-4.1 | `openai:gpt-4.1` | openai | General purpose |
| GPT-4o | `openai:gpt-4o` | openai | Fast, cost-effective |
| O3 | `openai:o3` | openai | Complex reasoning (with `reasoning_effort`) |

### O3 Reasoning Configuration

When using O3, configure reasoning effort via `llm_extra_config`:

```json
{
  "llm_extra_config": {
    "extra_config_type": "openai_config",
    "reasoning_effort": "high"
  }
}
```

Valid reasoning_effort values: `minimal`, `low`, `medium`, `high`

### AWS Bedrock Models (Claude)

Bedrock models are region-specific. Choose based on your data residency requirements.

**US Regions:**

| Name | Reference | Region |
|------|-----------|--------|
| Claude Sonnet 4.5 US East 1 | `bedrock_us-east-1:us.anthropic.claude-sonnet-4-5-20250929-v1:0` | us-east-1 |
| Claude Sonnet 4.5 US East 2 | `bedrock_us-east-2:us.anthropic.claude-sonnet-4-5-20250929-v1:0` | us-east-2 |
| Claude Sonnet 4.5 US West 1 | `bedrock_us-west-1:us.anthropic.claude-sonnet-4-5-20250929-v1:0` | us-west-1 |
| Claude Sonnet 4.5 US West 2 | `bedrock_us-west-2:us.anthropic.claude-sonnet-4-5-20250929-v1:0` | us-west-2 |

**EU Regions:**

| Name | Reference | Region |
|------|-----------|--------|
| Claude Sonnet 4.5 EU Central 1 | `bedrock_eu-central-1:eu.anthropic.claude-sonnet-4-5-20250929-v1:0` | eu-central-1 |
| Claude Sonnet 4.5 EU West 1 | `bedrock_eu-west-1:eu.anthropic.claude-sonnet-4-5-20250929-v1:0` | eu-west-1 |

**APAC Regions:**

| Name | Reference | Region |
|------|-----------|--------|
| Claude Sonnet 4.5 Tokyo | `bedrock_ap-northeast-1:jp.anthropic.claude-sonnet-4-5-20250929-v1:0` | ap-northeast-1 |
| Claude Sonnet 4.5 Sydney | `bedrock_ap-southeast-2:au.anthropic.claude-sonnet-4-5-20250929-v1:0` | ap-southeast-2 |

### Bedrock Configuration Options

```json
{
  "llm_extra_config": {
    "extra_config_type": "bedrock_config",
    "thinking": {
      "type": "enabled",
      "budget_tokens": 8192
    },
    "cache_instructions": true,
    "cache_tool_definitions": true,
    "cache_messages": false
  }
}
```

Options:
- `thinking`: Enable extended thinking with token budget (min 1024)
- `cache_instructions`: Cache system prompts for cost reduction
- `cache_tool_definitions`: Cache tool schemas
- `cache_messages`: Cache conversation history

---

## Cost Optimization

| Strategy | Implementation |
|----------|----------------|
| Use GPT-4o for simple tasks | Faster and cheaper than GPT-5 |
| Enable Bedrock caching | Reduces token costs for repeated calls |
| Minimize tool count | Fewer tool descriptions = fewer tokens |
| Use appropriate reasoning_effort | Don't use "high" unless needed |

## BYOM (Bring Your Own Model)

If using custom LLM credentials:

1. Set up credentials first:
   ```bash
   echo '{"name": "My OpenAI", "creds_type": "API_KEY", "api_key": "..."}' | \
     python -m cli llm creds-create
   ```

2. Create LLM config:
   ```bash
   echo '{
     "name": "My GPT-4o",
     "provider": "openai",
     "llm_credentials_id": "<creds-id>",
     "model_name": "gpt-4o"
   }' | python -m cli llm create
   ```

3. Use the new LLM in your agent config.

## Getting LLM Config IDs

```bash
# List all LLMs
python -m cli llm list

# Find specific LLM by name pattern
python -m cli llm list | jq '.data[] | select(.name | contains("GPT-5"))'
```

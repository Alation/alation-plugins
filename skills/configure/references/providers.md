# LLM Providers

This document describes supported LLM providers and their capabilities.

## Provider Overview

| Provider | Auth Type | BYOM Support | Notes |
|----------|-----------|--------------|-------|
| OpenAI | API_KEY | Yes | GPT models, o-series reasoning |
| AWS Bedrock | AWS | Yes | Claude models, region-specific |
| Azure OpenAI | AZURE | Yes | GPT models via Azure |
| Google Vertex AI | GCP | Yes | Gemini models |

## OpenAI

**Provider string:** `openai`

**Supported Models:**
- `gpt-5-2025-08-07` - Latest flagship model
- `gpt-4.1` - Previous generation flagship
- `gpt-4o` - Fast, cost-effective
- `gpt-4o-mini` - Smallest/cheapest
- `o3` - Reasoning model (supports reasoning_effort)
- `o4-mini` - Smaller reasoning model

**Extra Configuration:**
```json
{
  "extra_config_type": "openai_config",
  "reasoning_effort": "high"  // for o-series models
}
```

**BYOM Setup:**
1. Create API_KEY credentials with your OpenAI API key
2. Create LLM config with `provider: "openai"`, `model_name: "<model>"`

## AWS Bedrock

**Provider string:** `bedrock` or `bedrock_<region>` (e.g., `bedrock_us-west-2`)

**Supported Models:**
- Claude Sonnet 4.5: `anthropic.claude-sonnet-4-5-20250929-v1:0`
- Claude Sonnet 4: `anthropic.claude-sonnet-4-20250514-v1:0`
- Claude 3.5 Sonnet: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Claude 3 Sonnet: `anthropic.claude-3-sonnet-20240229-v1:0`

**Note:** Model availability varies by region. Use region-specific inference profiles (us., eu., jp., au., apac.) for cross-region access.

**Extra Configuration:**
```json
{
  "extra_config_type": "bedrock_config",
  "thinking": {
    "type": "enabled",
    "budget_tokens": 8192
  },
  "guardrail": {
    "guardrail_identifier": "abc123",
    "guardrail_version": "1",
    "trace": "enabled"
  },
  "cache_instructions": true,
  "cache_tool_definitions": true,
  "cache_messages": false
}
```

**BYOM Setup:**
1. Create AWS credentials with access key, secret key, and region
2. Create LLM config with `provider: "bedrock"`, `model_name: "<model-id>"`
3. Provider will be resolved to region-specific (e.g., `bedrock_us-west-2`)

## Azure OpenAI

**Provider string:** `azure`

**Setup Requirements:**
- Azure OpenAI resource endpoint
- API version (e.g., `2024-10-21`)
- Either API key or service principal credentials

**BYOM Setup:**
1. Create AZURE credentials:
   ```json
   {
     "name": "Azure OpenAI",
     "creds_type": "AZURE",
     "azure_endpoint": "https://myresource.openai.azure.com/",
     "api_version": "2024-10-21",
     "api_key": "..."
   }
   ```
2. Create LLM config with your deployment name as `model_name`

## Google Vertex AI / Gemini

**Provider string:** `gemini` (for API key) or `vertexai` (for service account)

**Supported Models:**
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-2.0-flash-exp`

**BYOM Setup (API Key):**
```json
{
  "name": "Gemini API",
  "creds_type": "GCP",
  "api_key": "..."
}
```

**BYOM Setup (Service Account):**
```json
{
  "name": "Vertex AI",
  "creds_type": "GCP",
  "gcp_project": "my-project-id",
  "gcp_location": "us-central1",
  "gcp_service_account": { /* service account JSON */ }
}
```

## Validation

Before using BYOM credentials, validate them:

```bash
# List available models (if supported by provider)
python -m cli llm creds-validate <id> --provider openai

# Validate specific model
python -m cli llm creds-validate <id> --provider openai --model gpt-4o
```

Validation modes:
- Without `--model`: Lists available models (if provider supports listing)
- With `--model`: Makes a minimal inference call to verify access

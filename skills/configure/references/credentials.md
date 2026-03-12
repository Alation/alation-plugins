# LLM Credentials Setup Guide

This guide covers setting up credentials for BYOM (Bring Your Own Model) configurations.

## Credential Types

### API_KEY - OpenAI, Anthropic, OpenAI-compatible providers

For providers that use API key authentication.

**Required Fields:**
- `name`: Display name for the credentials
- `creds_type`: `"API_KEY"`
- `api_key`: Your API key

**Optional Fields:**
- `base_url`: Custom base URL for OpenAI-compatible providers

**Examples:**

OpenAI:
```json
{
  "name": "My OpenAI Key",
  "creds_type": "API_KEY",
  "api_key": "sk-proj-..."
}
```

Anthropic Direct (not Bedrock):
```json
{
  "name": "Anthropic API",
  "creds_type": "API_KEY",
  "api_key": "sk-ant-..."
}
```

DeepSeek (OpenAI-compatible):
```json
{
  "name": "DeepSeek",
  "creds_type": "API_KEY",
  "api_key": "...",
  "base_url": "https://api.deepseek.com/v1"
}
```

Together AI:
```json
{
  "name": "Together AI",
  "creds_type": "API_KEY",
  "api_key": "...",
  "base_url": "https://api.together.xyz/v1"
}
```

### AWS - AWS Bedrock

For accessing Claude and other models via AWS Bedrock.

**Required Fields:**
- `name`: Display name
- `creds_type`: `"AWS"`
- `aws_access_key_id`: AWS access key ID
- `aws_secret_access_key`: AWS secret access key
- `aws_region`: AWS region (e.g., `us-west-2`, `eu-central-1`)

**Optional Fields:**
- `aws_session_token`: For temporary credentials (STS)

**Example:**
```json
{
  "name": "AWS Bedrock US West",
  "creds_type": "AWS",
  "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "aws_region": "us-west-2"
}
```

**IAM Policy Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

### AZURE - Azure OpenAI

For Azure OpenAI deployments.

**Required Fields:**
- `name`: Display name
- `creds_type`: `"AZURE"`
- `azure_endpoint`: Your Azure OpenAI endpoint URL
- `api_version`: API version (e.g., `2024-10-21`)
- One of:
  - `api_key`: Azure API key
  - Service principal: `azure_client_id`, `azure_client_secret`, `azure_token_url`

**Example (API Key):**
```json
{
  "name": "Azure OpenAI",
  "creds_type": "AZURE",
  "azure_endpoint": "https://myresource.openai.azure.com/",
  "api_version": "2024-10-21",
  "api_key": "..."
}
```

**Example (Service Principal):**
```json
{
  "name": "Azure OpenAI SP",
  "creds_type": "AZURE",
  "azure_endpoint": "https://myresource.openai.azure.com/",
  "api_version": "2024-10-21",
  "azure_client_id": "...",
  "azure_client_secret": "...",
  "azure_token_url": "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token"
}
```

### GCP - Google Vertex AI / Gemini

For Google's AI models.

**Required Fields:**
- `name`: Display name
- `creds_type`: `"GCP"`
- One of:
  - `api_key`: Gemini API key
  - Service account: `gcp_project`, `gcp_location`, `gcp_service_account`

**Example (API Key):**
```json
{
  "name": "Gemini API",
  "creds_type": "GCP",
  "api_key": "..."
}
```

**Example (Service Account):**
```json
{
  "name": "Vertex AI",
  "creds_type": "GCP",
  "gcp_project": "my-gcp-project",
  "gcp_location": "us-central1",
  "gcp_service_account": {
    "type": "service_account",
    "project_id": "my-gcp-project",
    "private_key_id": "...",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "...",
    "client_id": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

## Security Notes

1. **Credentials are stored encrypted** - API keys and secrets are encrypted at rest
2. **Never commit credentials** - Use environment variables or secure input
3. **Truncated display** - When viewing credentials, sensitive values show only last 4 characters
4. **Validate before use** - Always validate credentials before creating LLM configs

## CLI Commands

```bash
# Create credentials
echo '<json>' | python -m cli llm creds-create

# List credentials (shows truncated secrets)
python -m cli llm creds-list

# Validate credentials
python -m cli llm creds-validate <id> --provider <provider>

# Update credentials (e.g., rotate API key)
echo '{"api_key": "new-key..."}' | \
  python -m cli llm creds-update <id>

# Delete credentials
python -m cli llm creds-delete <id>
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "api_key is required for API_KEY creds type" | Missing api_key field | Add api_key to JSON |
| "aws_region is required for AWS creds type" | Missing AWS region | Add aws_region field |
| Validation fails with 401 | Invalid credentials | Check API key/secret |
| Validation fails with 403 | Insufficient permissions | Check IAM policy/roles |
| "Model not found" | Invalid model name | Check provider's model list |

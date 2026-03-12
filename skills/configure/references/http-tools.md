# HTTP Tools Guide

HTTP tools allow agents to call external HTTPS endpoints.

## Overview

HTTP tools enable:
- Calling REST APIs
- Webhook integrations
- External service lookups
- Custom business logic endpoints

## Configuration Structure

```json
{
  "name": "Display Name",
  "description": "What this tool does (shown to LLM)",
  "function_name": "unique_function_name",
  "tool_type": "HTTP",
  "http_config": {
    "url": "https://api.example.com/v1/resource/{param}",
    "method": "GET|POST|PUT|PATCH|DELETE",
    "timeout_seconds": 30
  },
  "auth_config": { /* see Auth section */ },
  "input_parameter_schema": { /* JSON Schema */ }
}
```

## URL Templates

URLs can include path parameters using `{param}` syntax:

```
https://api.example.com/users/{user_id}
https://api.example.com/v1/{resource_type}/{resource_id}
```

**Requirements:**
- Must use HTTPS (HTTP not allowed)
- Cannot use IP addresses (domain names only)
- Cannot point to localhost
- Path parameters must be defined in `input_parameter_schema`
- Path parameters must be in the `required` array

## HTTP Methods

| Method | Use Case | Request Body |
|--------|----------|--------------|
| GET | Retrieve data | No |
| POST | Create resource / Send data | Yes |
| PUT | Replace resource | Yes |
| PATCH | Partial update | Yes |
| DELETE | Remove resource | No |

## Authentication Types

### API_KEY

API key sent in header or query parameter.

```json
{
  "auth_type": "API_KEY",
  "auth_location": "header",  // or "query"
  "auth_key": "X-API-Key",    // header name or query param name
  "api_key": "your-api-key"
}
```

### BEARER

Bearer token in Authorization header.

```json
{
  "auth_type": "BEARER",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### BASIC

HTTP Basic authentication.

```json
{
  "auth_type": "BASIC",
  "username": "user",
  "password": "pass"
}
```

### OAUTH2

OAuth 2.0 client credentials flow.

```json
{
  "auth_type": "OAUTH2",
  "client_id": "...",
  "client_secret": "...",
  "token_url": "https://auth.example.com/oauth/token",
  "scope": "read write"  // optional
}
```

### NONE

No authentication (for public endpoints).

```json
{
  "auth_type": "NONE"
}
```

## Input Parameter Schema

JSON Schema defining the tool's input parameters:

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The user ID to look up"
    },
    "include_details": {
      "type": "boolean",
      "description": "Whether to include detailed info",
      "default": false
    }
  },
  "required": ["user_id"]
}
```

**Best Practices:**
- Always include descriptions for parameters
- Mark path parameters as required
- Use appropriate types (string, number, boolean, array, object)
- Provide defaults for optional parameters

## Examples

### GET with Path Parameter

```json
{
  "name": "Customer Lookup",
  "description": "Look up customer details by ID",
  "function_name": "lookup_customer",
  "tool_type": "HTTP",
  "http_config": {
    "url": "https://api.crm.com/v1/customers/{customer_id}",
    "method": "GET",
    "timeout_seconds": 30
  },
  "auth_config": {
    "auth_type": "API_KEY",
    "auth_location": "header",
    "auth_key": "X-API-Key",
    "api_key": "..."
  },
  "input_parameter_schema": {
    "type": "object",
    "properties": {
      "customer_id": {
        "type": "string",
        "description": "Customer ID to look up"
      }
    },
    "required": ["customer_id"]
  }
}
```

### POST with Request Body

```json
{
  "name": "Create Ticket",
  "description": "Create a support ticket",
  "function_name": "create_ticket",
  "tool_type": "HTTP",
  "http_config": {
    "url": "https://api.support.com/v2/tickets",
    "method": "POST",
    "timeout_seconds": 30
  },
  "auth_config": {
    "auth_type": "BEARER",
    "token": "..."
  },
  "input_parameter_schema": {
    "type": "object",
    "properties": {
      "subject": {
        "type": "string",
        "description": "Ticket subject"
      },
      "description": {
        "type": "string",
        "description": "Detailed description"
      },
      "priority": {
        "type": "string",
        "enum": ["low", "medium", "high"],
        "description": "Ticket priority"
      }
    },
    "required": ["subject", "description"]
  }
}
```

### Webhook (No Auth)

```json
{
  "name": "Slack Alert",
  "description": "Send alert to Slack channel",
  "function_name": "send_slack_alert",
  "tool_type": "HTTP",
  "http_config": {
    "url": "https://hooks.slack.com/services/T00/B00/xxx",
    "method": "POST",
    "timeout_seconds": 10
  },
  "auth_config": {
    "auth_type": "NONE"
  },
  "input_parameter_schema": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "Message to send"
      }
    },
    "required": ["text"]
  }
}
```

## Security Considerations

1. **HTTPS Only** - All URLs must use HTTPS
2. **No IP Addresses** - Must use domain names for SSRF protection
3. **No Localhost** - Cannot call internal services
4. **Timeout Limits** - Max 60 seconds per request
5. **Credential Storage** - Auth credentials are encrypted at rest

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "URL must use HTTPS" | HTTP URL provided | Change to HTTPS |
| "URL cannot use IP addresses" | IP in URL | Use domain name |
| "Path parameters not found" | Missing schema property | Add parameter to schema |
| "must be in required array" | Path param not required | Add to required array |
| 401/403 response | Auth failure | Check credentials |
| Timeout | Slow endpoint | Increase timeout_seconds |

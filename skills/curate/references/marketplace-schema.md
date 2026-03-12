# Marketplace Spec JSON Schema

The marketplace API accepts a `MarketplaceBody` object. The top-level key is `marketplace`.

## MarketplaceBody

```json
{
  "marketplace": {
    "marketplaceId": "string (required)",
    "contactEmail": "string (required)",
    "contactName": "string (required)",
    "dataProductRequirementsSchema": {},
    "heroBackgroundColor": "string (CSS color, e.g. '#FFFFFF')",
    "en": {
      "name": "string (required)",
      "description": "string",
      "shortDescription": "string",
      "heroImage": "string (URL)"
    },
    "badges": [
      {
        "check": "string (natural language description of the quality check)",
        "displayName": {
          "en": "string (badge label shown to users)"
        },
        "key": "string (spec field path, e.g. 'product.description')",
        "type": "static"
      }
    ],
    "minimumStandard": [
      {
        "check": "string (natural language description of the required standard)",
        "displayName": {
          "en": "string (standard label shown to users)"
        },
        "key": "string (spec field path, e.g. 'product.contactEmail')",
        "type": "static"
      }
    ]
  }
}
```

## Field Details

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `marketplaceId` | string | Yes | Unique identifier for the marketplace (e.g., `sales_marketplace`) |
| `contactEmail` | string | Yes | Contact email for the marketplace owner |
| `contactName` | string | Yes | Contact name for the marketplace owner |
| `dataProductRequirementsSchema` | object | No | JSON schema defining requirements for products in this marketplace |
| `heroBackgroundColor` | string | No | CSS color for the marketplace hero section |

### Localized Fields (`en`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name of the marketplace |
| `description` | string | No | Full description of the marketplace |
| `shortDescription` | string | No | Brief description shown in listings |
| `heroImage` | string | No | URL to the marketplace banner image |

### Badges

Badges are quality indicators displayed on products. They do NOT block publishing -- they are informational.

| Field | Type | Description |
|-------|------|-------------|
| `check` | string | Natural language description of what the badge checks |
| `displayName.en` | string | Label shown to users on the product card |
| `key` | string | Spec field path this badge evaluates (e.g., `product.description`) |
| `type` | string | Always `"static"` for now |

### Minimum Standards

Minimum standards are quality gates. Products that fail these checks **cannot be published** to the marketplace.

| Field | Type | Description |
|-------|------|-------------|
| `check` | string | Natural language description of the required standard |
| `displayName.en` | string | Label shown to users when the check fails |
| `key` | string | Spec field path this standard evaluates |
| `type` | string | Always `"static"` for now |

## Response Schema (Marketplace Object)

When reading a marketplace, the response includes additional fields:

```json
{
  "external_marketplace_id": "string",
  "spec": { "marketplace": { ... } },
  "spec_yaml": "string (YAML representation)",
  "products": [
    {
      "product_id": "string",
      "version_id": "string",
      "status": "draft|ready",
      "spec_json": { "product": { ... } },
      "spec_yaml": "string",
      "ts_created": "datetime",
      "ts_updated": "datetime"
    }
  ]
}
```

## Example: Full Marketplace Spec

```json
{
  "marketplace": {
    "marketplaceId": "sales_marketplace",
    "contactEmail": "allie@alation.com",
    "contactName": "Allie",
    "dataProductRequirementsSchema": {},
    "heroBackgroundColor": "#FFFFFF",
    "en": {
      "name": "Sales Data",
      "description": "Sales datasets including ARR, new sales, renewals, and churn.",
      "shortDescription": "Sales data marketplace",
      "heroImage": "https://example.com/banner.png"
    },
    "badges": [
      {
        "check": "The description of the product should describe where the data originated",
        "displayName": {"en": "Origins"},
        "key": "product.description",
        "type": "static"
      }
    ],
    "minimumStandard": [
      {
        "check": "Product must have a contact email",
        "displayName": {"en": "Has a contact email"},
        "key": "product.contactEmail",
        "type": "static"
      },
      {
        "check": "Has declared a support response time SLA in the description",
        "displayName": {"en": "Has a support SLA"},
        "key": "product.description",
        "type": "static"
      }
    ]
  }
}
```

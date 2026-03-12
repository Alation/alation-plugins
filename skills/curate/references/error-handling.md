# Error Handling

## Data Product Errors

### HTTP Status Codes

#### 400 Bad Request
**Cause:** Malformed request body or missing required fields.

**Recovery:**
1. Check the JSON spec is valid (no trailing commas, proper quoting)
2. Verify required fields: `productId`, `version`, `contactEmail`, `contactName`, `en.name`
3. If using `check-standards`, ensure both `--spec` and `--standards` files exist and are valid JSON
4. The standards file must be a JSON array

#### 403 Forbidden
**Cause:** Authentication failed or user lacks permissions.

**Recovery:**
1. Run `python -m cli setup check` to diagnose authentication status
2. If auth is the issue, use the setup skill to re-authenticate
3. Confirm the user has product admin or editor role
4. For localhost, no auth is required

#### 404 Not Found
**Cause:** The specified product ID or version ID does not exist.

**Recovery:**
1. Run `list` to see available products
2. Check for typos in the product ID (IDs are case-sensitive and namespaced, e.g., `finance:sales`)
3. Use `get <product_id>` to see available versions before using `get-version`

#### 422 Unprocessable Entity
**Cause:** Product fails marketplace quality standards (typically seen when publishing).

**Recovery:**
1. Run `check-standards` to identify which standards fail
2. Fix the product spec to address each failing check
3. Update the product with the fixed spec
4. Retry the operation

### Data Product API Error Codes

#### 30006 - Failed to get a valid connector configuration
**Cause:** The `deliverySystems` URI in your data product does not exactly match any configured connector.

**Most likely reason:** You modified the URI from the catalog instead of using it exactly as provided. Common mistakes include:
- Adding database parameters (e.g., `&db=MY_DATABASE`)
- Changing warehouse names
- Modifying host or port values

**Recovery:**
1. Fetch the source table's catalog object to get the exact URI
2. Extract the exact `ds.ocf_configuration.uri` value
3. Compare character-by-character with your data product's `deliverySystems.<name>.uri`
4. Update the data product to use the exact URI from the catalog (no modifications)

### Common Scenarios

**Version status stuck on "draft":**
Use `update-version` to change status to `ready`:
```bash
python -m cli product update-version <product_id> <version_id> --status ready
```

**Cannot publish to marketplace:**
The product version must be `ready` (not `draft`). Also check marketplace minimum standards using `check-standards`.

**Update changes not visible:**
The `update` command updates the product spec. If you need to change version metadata (like status), use `update-version` instead. These are separate operations.

**Product ID format:**
Product IDs use a namespace:name format (e.g., `finance:quarterly_sales`). The namespace groups related products. Both parts are required.

---

## Marketplace Errors

### HTTP Status Codes

#### 400 Bad Request
**Cause:** Malformed request body or missing required fields.

**Recovery:**
1. Check the JSON spec is valid (common issue: trailing commas, unquoted keys)
2. Verify required fields are present: `marketplaceId`, `contactEmail`, `contactName`, `en.name`
3. Check that `badges` and `minimumStandard` arrays contain valid objects with `check`, `displayName`, `key`, and `type` fields

#### 403 Forbidden
**Cause:** Authentication failed or user lacks permissions.

**Recovery:**
1. Run `python -m cli setup check` to diagnose authentication status
2. If auth is the issue, use the setup skill to re-authenticate
3. Confirm the user has marketplace admin or maintainer role
4. For localhost, no auth is required

#### 404 Not Found
**Cause:** The specified marketplace or product ID does not exist.

**Recovery:**
1. Run `list` to see available marketplaces
2. Check for typos in the marketplace ID
3. The ID is case-sensitive

#### 422 Unprocessable Entity
**Cause:** When publishing, the data product does not meet the marketplace's minimum standards.

**Recovery:**
1. Get the marketplace to see its `minimumStandard` requirements:
   ```bash
   python -m cli marketplace get --marketplace <id>
   ```
2. Use `python -m cli product check-standards` to see which checks fail
3. Update the data product to meet the standards
4. Retry publishing

### Common Scenarios

**Publishing fails silently:**
If `publish` returns success but the product doesn't appear in `list-products`, verify the product version status is `ready` (not `draft`). Use `python -m cli product update-version` to change status.

**Search returns no results:**
The search endpoint uses AI to process natural language queries. Try:
- More specific queries with product names or data types
- Broader queries if being too specific
- Verify products are actually published in the marketplace with `list-products`

**Marketplace delete fails:**
A marketplace with published products may need products unpublished first. Run `list-products` and `unpublish` each product before deleting the marketplace.

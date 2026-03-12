# Tool Error Codes Reference

Standard error codes returned by Alation AI tools. These indicate user-fixable errors that can be addressed without code changes.

## Error Code Ranges

| Range | Category |
|-------|----------|
| 00000 | Unknown/General |
| 10000-19999 | Query Execution |
| 20000-29999 | Context/Catalog Access |
| 30000-39999 | Data Products |
| 40000-49999 | SQL Evaluation |
| 50000-59999 | Catalog Objects |
| 60000-69999 | Billing/Licensing |

## Query Execution Errors (10000-19999)

### 10001 - QUERY_DATA_PRODUCT_AUTH_ID_NOT_PROVIDED
A valid `auth_id` was not provided for the data product query.

**Solution:** Provide a valid authentication credential ID when executing SQL against a data product.

```json
{
  "sql": "SELECT * FROM table",
  "data_product_id": "...",
  "auth_id": "your-auth-credential-id"
}
```

### 10003 - QUERY_CREDENTIALS_NOT_FOUND_FOR_AUTH_ID
No credentials were found for the given auth ID.

**Solution:** Verify the auth_id exists and you have access to it. Check credential configuration.

### 10010 - QUERY_SERVICE_ERROR
Error returned by the query service/connector.

**Solution:** Check the error message for details. May indicate:
- Invalid SQL syntax
- Table/column not found
- Permission denied on database
- Connection timeout

### 10011 - QUERY_SERVICE_CONNECTOR_CONFIGURATION_ERROR
The connector configuration is invalid.

**Solution:** Verify the data product's connector configuration. Contact an admin to fix the connector setup.

## Context/Catalog Access Errors (20000-29999)

### 20001 - CONTEXT_VALIDATION_ERROR
The context request validation failed (e.g., invalid signature format).

**Solution:** Check the signature format matches the expected schema. Refer to `get_signature_creation_instructions_tool` for correct format.

### 20002 - CONTEXT_ACCESS_DENIED
Access denied to context/catalog resources.

**Solution:** Verify you have permission to access the requested catalog objects. Contact your Alation admin for access.

### 20003 - CONTEXT_RESOURCE_NOT_FOUND
The requested context/catalog resource was not found.

**Solution:** Verify the object ID exists. The resource may have been deleted or moved.

## Data Product Errors (30000-39999)

### 30001 - DATA_PRODUCT_INVALID
The specified data product is invalid or malformed.

**Solution:** Check the data product configuration. May need to be fixed by an admin.

### 30002 - DATA_PRODUCT_NOT_FOUND
The specified data product was not found.

**Solution:** Verify the data_product_id is correct. The data product may have been deleted.

### 30003 - DATA_PRODUCT_EVALUATION_ALREADY_RUNNING
Data Product Evaluation is already running.

**Solution:** Wait for the current evaluation to complete before starting a new one.

### 30004 - DATA_PRODUCT_EVALUATION_SET_IS_EMPTY
Data Product Evaluation Set is empty.

**Solution:** Add evaluation cases to the set before running evaluation.

### 30005 - DATA_PRODUCT_ACTIVE_REVISION_JOB_NOT_FOUND
Data Product Revision Job is not active or found.

**Solution:** Start a new revision job before trying to finalize.

### 30006 - DATA_PRODUCT_CONNECTOR_CONFIGURATION_ERROR
Data Product connector configuration is invalid.

**Solution:** Check the data product's connector settings. Contact an admin to fix configuration.

## SQL Evaluation Errors (40000-49999)

### 40001 - SQL_EVAL_SET_INVALID
The provided SQL evaluation set is invalid or malformed.

**Solution:** Check the evaluation set structure matches the expected schema.

### 40002 - SQL_EVAL_CASE_INVALID
The provided SQL evaluation case is invalid or malformed.

**Solution:** Verify the case has required fields: question, expected SQL, etc.

## Catalog Object Errors (50000-59999)

### 50001 - SCHEMA_NOT_FOUND
The specified schema was not found.

**Solution:** Verify the schema ID exists in the catalog.

### 50002 - TABLE_NOT_FOUND
The specified table was not found.

**Solution:** Verify the table ID exists and you have access.

### 50003 - COLUMN_NOT_FOUND
The specified column was not found.

**Solution:** Verify the column ID exists on the expected table.

### 50004 - CUSTOM_FIELD_NOT_FOUND
The specified custom field was not found.

**Solution:** Verify the custom field name is correct. Custom fields are case-sensitive.

## Billing/Licensing Errors (60000-69999)

### 60001 - TOOL_CALL_QUOTA_EXCEEDED
Customer doesn't have any more tool calls left.

**Solution:** Contact your Alation admin about quota limits. Wait for quota reset or upgrade plan.


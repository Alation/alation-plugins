# Error Recovery Playbook

Detailed error handling strategies for data product queries.

## Column Not Found / Unknown Column

**Symptoms:**
- Error message contains "column not found" or "unknown column"
- SQL execution fails with reference to specific column name

**Recovery steps:**
1. Re-fetch schema with `--schema-only` flag
2. Check exact column name (case-sensitive)
3. Column might be in a different record set - review all available tables
4. Look for similar column names (typos, abbreviations)
5. Record as `schema_quirk` if naming is non-obvious

## Timeout / Query Too Slow

**Symptoms:**
- Request times out after 60 seconds
- Error message mentions timeout or execution limit

**Recovery steps:**
1. Add or reduce LIMIT clause (start with LIMIT 100)
2. Remove unnecessary columns from SELECT (avoid SELECT *)
3. Add more specific WHERE filters to reduce data scanned
4. Check if GROUP BY is producing too many groups
5. Consider using `execute-async` for large datasets

## Permission Denied / Forbidden

**Symptoms:**
- HTTP 403 error
- Error mentions "forbidden" or "insufficient permissions"

**This is a fatal error.** Recovery:
1. Inform the user they may need different permissions
2. Check if the product has restricted access
3. Suggest alternative data products if available
4. Do NOT retry - this won't resolve without user action

**User message template:**
> "I don't have permission to query this data product. You may need to request access or try a different data source. Would you like me to search for alternative products?"

## Product Not Found

**Symptoms:**
- HTTP 404 error
- Error mentions "not found" or "does not exist"

**Recovery steps:**
1. Verify the product_id is spelled correctly
2. List available products to find correct ID
3. The product may have been renamed, moved, or deleted
4. Search for similar products by keyword

## Syntax Error

**Symptoms:**
- SQL parsing error
- Error mentions "syntax error" or "unexpected token"

**Recovery steps:**
1. Review SQL for common issues:
   - Missing quotes around string literals
   - Mismatched parentheses
   - Invalid function names
   - Missing commas in SELECT list
2. Validate SQL before retrying (use `validate` command)
3. Simplify query and add complexity back incrementally

## Empty Results

**Not an error**, but may indicate issues:
1. Filters are too restrictive
2. Data doesn't exist for the criteria
3. Column values don't match expected format (case-sensitivity, spelling)

**Communicate to user:**
> "The query returned no results. This could mean no data matches your criteria. Would you like me to try a broader query?"

**Potential adjustments:**
- Remove or broaden filters
- Check if filter values need different case/format
- Verify date ranges contain data

## Authentication Failed

**Symptoms:**
- `AUTH_ERROR:` prefix in CLI output with exit code 2
- HTTP 401 or 403 error

**This is a fatal error.** Recovery:
1. Run `python -m cli setup check` to diagnose the issue
2. Use the setup skill to fix it (expired token → re-login, bad creds → reconfigure)
3. Do NOT retry without valid credentials

**User message template:**
> "Authentication failed. Let me check the setup status to diagnose the issue."

## Rate Limited

**Symptoms:**
- HTTP 429 error
- Error mentions "rate limit" or "too many requests"

**Recovery steps:**
1. Wait a few seconds before retrying
2. If pattern persists, space out requests
3. Consider batching multiple questions into single queries

## Connection Error

**Symptoms:**
- Network timeout or connection refused
- DNS resolution failure

**Recovery steps:**
1. Check `base_url` is correct in `credentials.local`
2. Verify network connectivity to Alation instance
3. Instance may be temporarily unavailable - retry after a minute

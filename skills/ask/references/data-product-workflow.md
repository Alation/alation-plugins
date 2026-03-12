# Data Product Query Workflow

Detailed workflow for querying data products via `python -m cli query`.

## Prerequisite: Product ID

This workflow assumes you already have a data product ID. If the user hasn't identified a product yet, use the **explore** skill to find one before proceeding.

## Step 1: Fetch and Analyze Schema

```bash
python -m cli query get --product "<product_id>" --schema-only
```

**Analyze the schema:**
- Each record set includes a `qualified_name` field (e.g., `"LAUREL.SUPERSTORE.ORDERS"`) — use this in SQL queries
- Note exact column names (case-sensitive)
- Understand data types for aggregations

## Step 2: Generate SQL Query

Based on the schema, construct a SQL query:
1. Use the `qualified_name` from schema for table references
2. Use exact column names from the schema
3. Apply appropriate aggregations (COUNT, SUM, AVG, etc.)
4. Add WHERE, GROUP BY, ORDER BY as needed
5. Always include LIMIT (default 100)

**When the question is ambiguous:**
- Prefer the most specific matching column (e.g., `customer_region` over `region` for customer questions)
- Explain your column/table choice to the user so they can correct you
- If no time frame is specified, don't add arbitrary date filters — query all available data

## Step 3: Execute the Query

```bash
python -m cli query execute --product "<product_id>" --sql "<your_sql_query>" --timeout 60
```

For long-running queries:
```bash
python -m cli query execute-async --product "<product_id>" --sql "<your_sql_query>"
```

## Step 4: Summarize Results

Transform raw query results into a clear, actionable insight.

## Validation (Optional)

```bash
python -m cli query validate --product "<product_id>" --sql "<your_sql_query>"
```

## Error Recovery Quick Reference

| Error | Quick Fix |
|-------|-----------|
| Table/Object not found | Use `qualified_name` from schema |
| Column not found | Re-fetch schema, check exact column name |
| Timeout | Add LIMIT, simplify query, use execute-async |
| Permission denied | Inform user, suggest alternatives |
| Product not found | Verify product_id; use **explore** skill to search if ID is wrong |
| Syntax error | Validate SQL, check string quotes |

See `error-recovery.md` for the full error handling playbook.

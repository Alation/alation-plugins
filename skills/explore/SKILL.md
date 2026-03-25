---
name: explore
description: "Use when the user wants to discover, find, or browse data assets in the Alation catalog, data products, or marketplaces. Triggers: search catalog, find tables, list data sources, browse schemas, show columns, what data do we have, what tables exist, explore database, describe table, what's in this data source, show me the schema, list schemas, list columns, what databases do we have, show table structure, describe this data source, find data products, list data products, what data products do we have, search products, show available products, what products are in the marketplace, browse marketplace, which product has sales data. Use this skill when the user wants to know what data exists, understand table/column structure, or find data products — not when they want actual query results or numbers. Not for answering data questions or running queries — use ask instead. Not for creating or managing data products — use curate instead."
---

# Explore

Find and explain where data lives in Alation, using user language (not Alation jargon), and return navigable catalog results.

## Behavior Contract

- Be concise: default to short answers and focused result lists.
- Use user terminology first, then map to Alation object types internally.
- Ask at most one clarifying question when needed.
- Do not run queries for totals/counts/trends in this skill.
- Include catalog `url` for each recommended result.

## Intent Mapping (Goal First)

Translate user goals into catalog discovery actions:

- "Where can I find X data?" -> keyword search, then refine by object type.
- "What data sources do we have?" -> list data sources.
- "What is inside source X?" -> browse source -> schemas -> tables -> columns.
- "Show me schema/table structure" -> browse hierarchy for that object.
- "Tell me about this table/column" -> describe specific object by ID.
- "What data products do we have?" -> list data products.
- "Which product has sales data?" -> search data products by keyword.
- "What's in this data product?" -> get product details and schema.
- "What marketplaces are available?" -> list marketplaces.
- "What products are in marketplace X?" -> list or search products in a marketplace.

If user says something broad like "show me sales data":
1. Treat as discovery by default (explore).
2. Search both catalog (`search "sales"`) and data products (`query search --query "sales"`).
3. Present results grouped: data products first (queryable), then catalog matches (browse-only).
4. If data products were found: "Want me to query one of these products for results?"
5. If only catalog matches: "I found tables but no queryable data product. Want to explore these further, or create a data product from one?"

## Internal Command Routing

Use these commands to execute the workflow:

| Goal | CLI Command |
|---|---|
| Keyword discovery | `python -m cli search "keyword" [--limit N] [--type <object_type>]` |
| List data sources | `python -m cli browse sources [--limit N] [--skip N]` |
| List schemas in source | `python -m cli browse schemas --ds-id ID [--limit N] [--skip N]` |
| List tables | `python -m cli browse tables --schema-id ID [--limit N] [--skip N]` or `--ds-id ID` |
| List columns | `python -m cli browse columns --table-id ID [--limit N] [--skip N]` or `--ds-id ID` |
| Describe object | `python -m cli browse describe --type {datasource\|schema\|table\|column} --id ID` |
| Hierarchical tree | `python -m cli browse tree --ds-id ID [--depth 1\|2\|3]` |
| List data products | `python -m cli query list [--limit N] [--skip N]` |
| Search data products | `python -m cli query search --query "keyword" [--marketplace EXTERNAL_MARKETPLACE_ID]` |
| Get product details/schema | `python -m cli query get --product ID [--schema-only]` |
| List marketplaces | `python -m cli marketplace list` |
| Get marketplace details | `python -m cli marketplace get --marketplace EXTERNAL_MARKETPLACE_ID` |
| List products in marketplace | `python -m cli marketplace products --marketplace EXTERNAL_MARKETPLACE_ID` |
| Search products in marketplace | `python -m cli marketplace search --marketplace EXTERNAL_MARKETPLACE_ID --query "keyword"` |

`search` type: Can be one of many options. The most common are "table", "column", "schema", "article", "glossary_term", "datasource", Use `--help` to see all the options.

`browse tree` depth: 1 = schemas only, 2 = schemas + tables, 3 = schemas + tables + columns.
Always pass `--depth 1` explicitly on unfamiliar sources — depth 3 on a large source can return hundreds of objects.

## Standard Workflow

1. Interpret the user goal in plain language.
2. Pick discovery path:
   - Unknown location -> search first (catalog search for tables/columns, product search for data products).
   - Known source/object -> browse hierarchy (for catalog) or get product details (for data products).
   - Known marketplace -> list or search products in that marketplace.
3. If required identifier is missing, list the parent level first (e.g., sources before schemas).
4. Return top relevant results with name, description, and URL. Include IDs only when the
   user will need to refer back to them. Translate Alation types into plain language
   (e.g., "database" not "datasource").
5. Offer one next step, then wait for confirmation.

## Data Product Discovery

Data products are queryable datasets published in Alation. They do not appear in catalog search results (`search` command), so use the dedicated product commands instead.

### Finding a data product

1. Start with `query search --query "keyword"` if the user describes what data they need.
2. Fall back to `query list` if the search term is too vague or returns nothing.
3. Use `query get --product ID --schema-only` to inspect tables and columns in a product.

### Marketplace browsing

Marketplaces are curated collections of data products. If the user mentions a marketplace or wants to browse published products:

1. `marketplace list` to find available marketplaces.
2. `marketplace products --marketplace EXTERNAL_MARKETPLACE_ID` or `marketplace search --marketplace EXTERNAL_MARKETPLACE_ID --query "keyword"` to browse within one. 

Always use the external marketplace ID to identify marketplaces.

### Handoff to ask

After the user identifies a data product, suggest querying it: "Want me to query this
product for results?" Then hand off to the **ask** skill with the product ID.

## Disambiguation

When search or browse returns multiple plausible matches, present the options and let the user choose. Show each option with its name, which data source it belongs to, and a brief description if available. Don't silently pick one — the user knows their data better than you.

Only skip this if the user already specified exactly what they want or there is a single obvious match.

## Response Format

Use this compact structure:

- One-line outcome statement.
- Up to 5 results (most relevant first), each with:
  - name
  - description (if available)
  - URL
- One optional next-step question.

## Not This Skill

Route away when the request is outside discovery:

- User wants numbers/analysis/results from data -> use `ask` (provide the product ID).
- User wants to create/manage data products, publish to marketplace -> use `curate`.
- User wants to create/manage agents, tools, LLMs, or connections -> use `configure`.

## Error and Fallback Handling

- Authentication/setup errors:
  - Suggest `python -m cli setup check`.
  - If still blocked, route to setup skill.
- No search results:
  - Retry with simpler keywords or synonyms.
  - Remove strict type filter.
  - Ask one clarifying question about business term/source system.
- Too many results:
  - Narrow by type (`table`/`column`) or source.
  - Use pagination via `--limit` and `--skip`.
- Missing IDs for browse commands:
  - Retrieve parent objects first; do not guess IDs.

## Common Mistakes

**Mistake:** Using search when the user names a specific data source.
Why it seems reasonable: search feels like a universal starting point.
Instead: Find that source via `browse sources`, then drill in with `browse tree` or `browse schemas`.

**Mistake:** Using `browse tree --depth 3` on a large or unfamiliar source.
Why it seems reasonable: showing everything at once feels thorough.
Instead: Start at `--depth 1`. Let the user tell you what to drill into.

**Mistake:** Describing every table when the user just asked what's there.
Why it seems reasonable: more detail seems more helpful.
Instead: List table names first. Only describe a specific table when the user picks one.

**Mistake:** Proceeding to another skill action without user confirmation.
Why it seems reasonable: anticipating the next step feels efficient.
Instead: Suggest one next step and wait. "Want me to query this data?" not "Let me query this for you."

**Mistake:** Using catalog `search` to find data products.
Why it seems reasonable: search feels like a universal starting point.
Instead: Data products don't appear in catalog search. Use `query search` or `query list` for data products.

**Mistake:** Using `product list` or `product get` for discovery.
Why it seems reasonable: they sound like discovery commands.
Instead: Those are management commands (raw spec JSON) used by the `curate` skill. For discovery, use `query list` and `query get` which return consumer-friendly views.

## Red Flags

- "Let me search for all tables" — search is keyword-based. To list tables, use browse.
- "I'll check the data source API" — all commands go through the CLI, never raw APIs.
- "I'll fetch all columns for this data source" — could be enormous. Drill down through schemas and tables first.
- "Let me show you everything at depth 3" — start at depth 1; go deeper only as needed.
- "Data products should show up in catalog search" — they don't. Use `query search` or `query list`.

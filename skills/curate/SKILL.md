---
name: curate
description: "Use when the user wants to create, update, or manage data products, publish or unpublish data products to a marketplace, manage marketplaces, enrich catalog metadata, add descriptions to tables or columns, set tags, set custom field values, check data product standards, manage product versions, or mark a version as ready. Also use for: product spec, product schema, delivery systems, record sets, marketplace badges, minimum standards, set up a new data product, define a product, annotate tables, enrich metadata. Use this skill any time the user mentions data products in a creation or management context, or wants to add/edit metadata on catalog objects. Not for querying data products — use ask. Not for browsing catalog — use explore. Not for creating data source connections — use configure."
---

# Curate

Manage data products, publish to marketplaces, and enrich catalog metadata.

## Routing

| User Intent | CLI Command | When to Use |
|---|---|---|
| Create/update/delete data products | `python -m cli product` | Managing product specs and versions |
| Publish/unpublish to marketplace | `python -m cli marketplace publish/unpublish` | Making products discoverable |
| Manage marketplaces themselves | `python -m cli marketplace` | Creating or configuring marketplaces |
| Add descriptions/tags/custom fields | `python -m cli enrich` | Enriching metadata on any catalog object |

## Not This Skill

- User wants to **query** a data product for answers → use `ask`
- User wants to **browse or search** data sources, the catalog, data products, or marketplaces → use `explore`
- User wants to **schedule** recurring queries against a product → use `automate`
- User wants to **create a data source connection** → use `configure`

Key distinction: `curate` manages data product definitions and metadata. `ask` runs queries against those products. "Create a data product" is `curate`. "Query a data product" is `ask`.

## Data Product Lifecycle

**First, check what you already have.** If a complete or near-complete spec is available (e.g. from `bi product-spec`, a user-provided JSON/YAML file, or a prior conversation step), use it as-is — do not discard its schema, record sets, or delivery systems. Only fall back to the empty-schema workflow when you are building a spec from scratch.

### When a spec is already available

1. **Review the spec** with the user. Confirm product ID, name, record sets, and schema look correct.
2. **Save the spec** as a JSON file (e.g. `spec.json`), then **create the product**:
   `python -m cli product create < spec.json`
   If the spec is in YAML (e.g. from `bi product-spec`), convert it to JSON before saving.
3. Continue to **Mark version ready** and **Publish** below.

### When building from scratch

1. **Create product** with minimal spec (`"schema": []`):
   `python -m cli product create < spec.json`
   See `references/product-schema.md` for the JSON schema.

2. **Discover columns** by querying the product (use the `ask` skill) or browsing the data source (use the `explore` skill).

3. **Update spec** with discovered schema:
   `python -m cli product update < updated_spec.json`

### After creation (both paths)

4. **Mark version ready:**
   `python -m cli product update-version PRODUCT_ID VERSION_ID --status ready`

5. **Publish to marketplace:**
   `python -m cli marketplace publish --marketplace EXTERNAL_MARKETPLACE_ID --product ID`

## Metadata Enrichment

- `python -m cli enrich list-fields` — see available custom fields
- `python -m cli enrich get-values --otype table --oid 123` — see current values
- `python -m cli enrich set-field --otype table --oid 123 --field-id 456 --value "description text"`
- Object types: `table`, `schema`, `attribute` (column), `data` (datasource)

## Common Mistakes

**Mistake:** Trying to publish a product whose version is still in "draft" status.
Why it seems reasonable: the product exists, so it should be publishable.
Instead: Check version status first. Mark it as "ready" before publishing.

**Mistake:** Setting `deliverySystems.type` to uppercase `"SQL"`.
Why it seems reasonable: the `dataAccess[].type` field IS uppercase.
Instead: `deliverySystems.type` must be lowercase `"sql"`. The `dataAccess[].type` must be uppercase `"SQL"`. Yes, this is inconsistent — see `references/product-schema.md`.

## Next Steps

After finishing curation, suggest next steps to the user — but don't proceed without
their go-ahead unless their original request already implies it.

- **After creating or updating a data product:** Share the product URL from the CLI response so the user can view it in the Alation UI.
- **After publishing a data product:** "Would you like to query this product? I can do that using the ask skill."
  If the user mentions recurring reports, suggest the **automate** skill to schedule queries.

## Red Flags
- "I'll populate the full schema upfront" — only when building from scratch. If a pre-populated spec was provided, use it as-is.
- "Let me set the product version to ready immediately" — only after the spec is complete and validated.
- "Let me strip the schema and start fresh" — if the spec already has schema/record sets, do not discard them.

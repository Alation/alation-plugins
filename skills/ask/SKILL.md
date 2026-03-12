---
name: ask
description: 'Use when the user asks a data question, wants to run a query against a data product, chat with an AI agent, or invoke a tool. Triggers: run SQL, run a query against a data product, ask agent, chat with agent, execute query, invoke tool, call tool, get answer, analyze data, how many, what is the total, count of, sum of, average, compare, trend, show me orders, pull revenue, what were sales, run this SELECT. A data product ID should be known before using this skill. If the user asks a vague data question and no product is identified, route through explore first to find the right product. Not for finding or browsing data products — use explore instead. Not for browsing catalog structure — use explore instead. Not for recurring/scheduled queries — use automate instead.'
---

# Ask

Answer data questions by querying data products, chatting with AI agents, or invoking tools.

## Routing

| User Intent | CLI Command | When to Use |
|---|---|---|
| Answer a data question | `python -m cli query execute` | User has a data product ID (or one was found via explore) |
| Inspect product schema before querying | `python -m cli query get --product ID --schema-only` | Internal prep to write correct SQL — not for user-facing schema discovery (use explore) |
| Multi-turn reasoning or analysis | `python -m cli chat send` | User wants to chat with a specific agent |
| Single-shot tool operation | `python -m cli tool call` | User wants one specific action |

**Default path:** For data questions, execute a query against a data product using `python -m cli query execute`. The product ID should be known — if not, use the **explore** skill to find the right product first. Only use `python -m cli chat` or `python -m cli tool` if no data product fits or the user explicitly asks for an agent or tool.

**Only Data Products can be queried.** If the user wants to query a raw table or database that isn't part of a data product, explain this limitation. Use **explore** to find an equivalent data product, or suggest **curate** to wrap the table in a new data product.

## Disambiguation

When a search or lookup returns multiple plausible matches — whether data products, tables, agents, or tools — present the options to the user with enough context to choose (name, description, and any distinguishing details). The user knows their data better than you do.

This matters because picking the wrong dataset doesn't just waste time — it can actively mislead the user. If you silently choose the wrong product, the user gets back numbers they'll trust and act on, with no indication they came from the wrong source.

Only skip this step if one result is an obviously better fit than the rest, or the user already specified exactly what to use.

For detailed step-by-step workflows, read:
- `references/data-product-workflow.md` — full query workflow with schema discovery and SQL patterns
- `references/agent-chat-workflow.md` — agent selection, streaming, multi-turn conversations
- `references/tool-invoke-workflow.md` — tool discovery, schema inspection, invocation

## Quick Reference

### Data Product Query (most common)
```
python -m cli query get --product ID --schema-only    # See tables/columns (if schema not yet known)
python -m cli query execute --product ID --sql "SELECT ..."  # Run query
python -m cli query validate --product ID --sql "SELECT ..."  # Validate without running (optional)
```
Product ID should be known before reaching this skill. If unknown, use the **explore** skill to search for and identify the right data product.

### Agent Chat
```
python -m cli agent list                                                           # See all agents (summary)
echo '{"message": "..."}' | python -m cli chat send alamigo_agent                  # Default agent (by ref)
echo '{"message": "..."}' | python -m cli chat send 957ed0b8-4b42-4d5b-9e07-...   # Custom agent (by UUID)
```
Default agents have `is_default: true` and a `default_ref` — use the ref name with `chat send`. Use `agent get <id>` for full config detail.

To continue a conversation (multi-turn), pass `--chat-id` from the previous response:
```
echo '{"message": "Now break it down by region"}' | python -m cli chat send alamigo_agent --chat-id <uuid>
```
Without `--chat-id`, each `chat send` starts a fresh conversation with no memory of prior messages.

### Tool Invocation
```
python -m cli tool list                          # See all tools (summary)
python -m cli tool schema TOOL_REF_OR_UUID       # Check tool parameters
echo '{"param": "value"}' | python -m cli tool call TOOL_REF_OR_UUID  # Invoke tool
```
See `configure/references/default-tools.md`. Use `python -m cli tool schema <ref>` for full parameter detail.

## Not This Skill

- User wants to **find, browse, or search** data sources, schemas, tables, or data products → use `explore`
- User wants to **create or manage** a data product → use `curate`
- User wants to **set up** an agent, tool, or LLM → use `configure`
- User wants to **schedule** a recurring query or report → use `automate`

## Schedule Requests → Automate

If the user mentions anything recurring, scheduled, daily, weekly, or automated — even casually like "can I get this every Monday?" — that's a workflow, not a one-off query. Guide them to the **automate** skill to build a flow and schedule it. Don't just run the query and leave the scheduling part unaddressed.

## Common Mistakes

**Mistake:** Trying to use Compose or a raw SQL endpoint to execute a query.
Why it seems reasonable: the user said "run this SQL."
Instead: Always use `python -m cli query execute` which routes through the proper execution API. There is no Compose API.

**Mistake:** Chatting with an agent when a direct data product query would suffice.
Why it seems reasonable: agents can answer questions too.
Instead: For straightforward data questions, data product queries are faster and more reliable.

**Mistake:** Invoking sql_execution_tool via tool-invoke for ad-hoc queries.
Why it seems reasonable: it's a SQL execution tool.
Instead: Use `python -m cli query execute` which handles product context, schema discovery, and error recovery.

**Mistake:** Searching for data products within the ask skill.
Why it seems reasonable: you need to find a product before querying it.
Instead: Use the **explore** skill to find products. The ask skill expects a product ID as input. If the user asks a data question and no product is known, route through explore first.

**Mistake:** Auto-selecting an agent or tool when multiple results match.
Why it seems reasonable: picking one and moving forward feels efficient and helpful.
Instead: Present the matches to the user with names, descriptions, and distinguishing details. Let them choose. Picking the wrong source doesn't just waste time — the user gets back results they'll trust and act on, with no indication the data came from the wrong place.

## Red Flags
- "I'll use Compose to run this query" — there is no Compose API. Use `python -m cli query execute`.
- "Let me call the API directly" — always use the CLI.
- "I don't know which data product to use, so I'll skip it" — route to the **explore** skill to find one first.

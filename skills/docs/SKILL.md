---
name: docs
description: 'Use when the user asks how to do something in the Alation product or asks about the Alation REST API, answered from official public docs with links. Triggers: how do I in Alation, Alation documentation, API endpoint, request body, API schema, OpenAPI, OAuth client registration, configure connector, metadata extraction, MDE, QLI, lineage setup, cloud vs customer-managed differences, API recipe, code example, doc error. Not for data in the user''s instance (tables, data products, query results) — use explore or ask. Not for creating agents, tools, or workflows — use configure or automate.'
---

# Docs

Answer Alation product and REST API questions from the official public docs, with cited links, using the Alation Docs MCP server (`https://documentation.alation.com/mcp`).

## Tools

Client may prefix names (e.g. `mcp__...alation-docs__search_alation_docs`). Match by suffix.

| Tool | Use |
|---|---|
| `search_alation_docs(query)` | Read-only semantic search over product docs, API guides, API reference, recipes. Returns title, link, page path, snippet. Start here. |
| `query_docs_filesystem_alation_docs(command)` | Read-only, stateless virtual shell over doc pages (`.mdx`) and OpenAPI specs. Supports `rg`, `grep`, `find`, `tree`, `ls`, `cat`, `head`, `tail`, `stat`, `wc`, `sort`, `uniq`, `cut`, `sed`, `awk`, `jq`. |
| `submit_feedback(path, feedback)` | NOT read-only. Sends doc feedback to Alation's docs team. See Feedback Policy. |

The server may also expose a resource `mintlify://skills/alation` (product skill guide). Read it if the client supports MCP resources. Use it for concepts and decision guidance only; its API endpoint paths are not reliable. Confirm any endpoint against the OpenAPI specs.

## Workflow

1. **Search first.** `search_alation_docs` with the user's key terms.
2. **Read the page.** For a hit at path `/x/y`, run `head -200 /x/y.mdx` or `rg -C 3 "term" /x/y.mdx` via the filesystem tool. Each call resets cwd to `/`; output truncates at 30KB, so avoid full `cat`.
3. **API questions:** inspect the OpenAPI spec with `jq`, e.g. `jq '.paths | keys' /openapi/openapi/alation-cloud-service-latest/data-products-api.json`, then drill into the path's request schema.
4. **Never guess paths.** Discover with `tree / -L 2`, `ls`, or search. Top-level: `/en/latest`, `/api-guides`, `/api-reference`, `/recipes`, `/openapi`.
5. **Answer concisely** with links. Convert a path to a URL by dropping `.mdx` and prefixing `https://documentation.alation.com`.

### Pick the right version

- Alation Cloud Service (ACS) → `alation-cloud-service-latest`
- Customer-managed → the matching folder (`2026-7-0-0-customer-managed`, `2026-4-0-0-customer-managed`)
- Unknown → ask, or default to cloud and state the assumption.

## Use Cases

- How-to product questions: configure a connector, run metadata extraction (MDE) or query log ingestion (QLI), set up lineage.
- API endpoint lookup: method, path, request and response schema (data products, custom fields, lineage, workflows, agents).
- OAuth client registration for plugin setup.
- Troubleshooting a failed plugin or API call by checking the documented contract.
- Comparing cloud vs customer-managed API differences.
- Finding recipes and code examples.
- Reporting a doc error (see Feedback Policy).

## Feedback Policy

- Never call `submit_feedback` without explicit user approval.
- Show the exact `path` and feedback text first, then wait for a yes.
- Never include customer data, instance URLs, credentials, tokens, IDs, or query results.
- Only for doc-content issues (incorrect, outdated, confusing, incomplete, broken example). Not for product support.

## If Docs Tools Are Unavailable

If the docs MCP tools are not present (portable agent-skills install, MCP not connected), say so. Then either fall back to the `ask` skill with `alamigo_agent` for product help, or suggest adding the server: `https://documentation.alation.com/mcp` (streamable HTTP, no auth). Do not fabricate doc content or links. Only cite links returned by the tools.

## Not This Skill

- User wants data from their instance (tables, data products, results) → use `explore` or `ask`
- User wants to create agents, tools, or LLMs → use `configure`
- User wants workflows or schedules → use `automate`
- User wants credentials or login → use `setup`

Docs describe the product in general. They know nothing about the user's instance.

## Common Mistakes

**Mistake:** Answering from memory.
Why it seems reasonable: the API looks familiar.
Instead: Search and read the page. Endpoints and fields change between versions.

**Mistake:** Citing a link that no tool returned.
Why it seems reasonable: the URL pattern is predictable.
Instead: Cite only links from search results or paths you confirmed exist.

**Mistake:** Using cloud docs for a customer-managed instance.
Why it seems reasonable: cloud is the default.
Instead: Confirm the deployment and use the matching version folder.

**Mistake:** Calling `submit_feedback` because the user complained about the docs.
Why it seems reasonable: they want it fixed.
Instead: Propose the exact text and wait for approval.

## Red Flags
- "I'll cat the whole file" — use `head`, `rg -C`, or `jq`.
- "I'll just send feedback" — approval first, always.
- "I'll paste the user's instance URL into feedback" — never.

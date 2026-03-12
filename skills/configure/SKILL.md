---
name: configure
description: 'Use when the user wants to create, modify, or manage AI agents, custom tools, LLM configurations, or data source connections. Triggers: create agent, configure agent, clone agent, publish agent as tool, create HTTP tool, create SMTP tool, add tool, configure LLM, bring your own model, BYOM, add data source, create connection, parameter bindings, tool authentication, set up agent, set up tool, manage LLM credentials. Key signal: if "set up" refers to infrastructure (agents, tools, LLMs, connections), use this skill. If "set up" refers to scheduling or automation, use automate. Not for scheduling or workflows — use automate. Not for creating data products — use curate.'
---

# Configure

Create and manage agents, tools, LLMs, and data source connections.

## Routing

| User Intent | CLI Command | When to Use |
|---|---|---|
| Manage AI agents | `python -m cli agent` | Create, clone, update, delete, publish agents |
| Manage tools | `python -m cli tool` | Create HTTP/SMTP tools, update, delete |
| Manage LLMs | `python -m cli llm` | BYOM setup, credentials, LLM configs |
| Manage data sources | `python -m cli datasource` | Create, update, delete data source connections |

## Not This Skill

- User wants to **schedule or automate** workflows → use `automate`
- User wants to **query data** or chat with an agent → use `ask`
- User wants to **create a data product** → use `curate`
- User wants to **browse** data source contents → use `explore`

Key distinction: `configure` creates and manages the infrastructure (agents, tools, LLMs, connections). `automate` uses that infrastructure in workflows. "Create an SMTP tool" is `configure`. "Set up a daily email report" is `automate`.

## Agent Configuration

### Creating an Agent

1. **Define the agent's purpose.** What should it do? Be specific — "answer sales questions against the superstore dataset" is better than "answer questions."

2. **Identify the data and context it needs.** What data products, data sources, or domain knowledge will the agent work with? Some of this becomes fixed tool bindings (step 5), some goes into the agent prompt (step 6).

3. **Select tools.** Browse available tools with `python -m cli tool list` and see `references/default-tools.md` for the selection matrix. Pick the combination needed for the agent's purpose. If a required tool doesn't exist (e.g., an HTTP or SMTP integration), create it first — see Tool Configuration below.

4. **Create the agent config** with the selected tools:
   `python -m cli agent create < config.json`
   Tip: if a default agent is close to what you need, clone it as a starting point:
   `python -m cli agent clone ID`

5. **Configure tool parameter bindings.** Bindings control how tool parameters get their values at runtime, constraining what the agent can do for reliability and consistency. For each tool parameter, choose a binding source:
   - **`fixed`**: The value is always the same. Use this to lock a tool to a specific resource like a `data_product_id`. The agent can't change it.
   - **`user`**: The caller provides the value when invoking the agent. Use for things like a recipient email or a `data_product_id` when the agent supports multiple products.
   - **`agent`**: The LLM decides the value based on the conversation. This is the default for most parameters — the agent interprets the user's message and figures out what to pass to the tool. For example, `data_product_id` can be agent-determined if the agent has a search tool and is expected to find the right product itself.

   Some parameters are hidden from the model (`x-hidden-from-model: true`) and must be `fixed` or `user` since the LLM can't see them to decide.

   See `references/bindings.md` for JSON structure, validation rules, and detailed patterns.

6. **Configure the agent prompt.** Describe the agent's high-level goal, its domain context, and when to use each of its tools. This is the agent's system prompt — it guides the LLM's behavior.

7. **Choose the LLM.** Pick a model powerful enough for the task. See `references/default-llms.md` for recommendations by use case.

8. **Test the agent.** Use the **ask** skill to send it a message and verify it works:
   `echo '{"message": "..."}' | python -m cli chat send <agent_uuid>`

### Publishing as Tool
`python -m cli agent publish ID` makes an agent callable by other agents.

## Tool Configuration

### Creating HTTP Tools
See `references/http-tools.md` for full guide. Key constraints:
- HTTPS only (no HTTP, no localhost, no IP addresses)
- Auth types: API_KEY, BEARER, BASIC, OAUTH2, NONE

### Creating SMTP Tools
See `references/smtp-tools.md` for provider-specific configs (SendGrid, AWS SES, Gmail, M365).

**Important:** Before creating a new tool, always list existing tools first with `python -m cli tool list`. An SMTP or HTTP tool may already be configured.

## LLM Configuration (BYOM)

1. **Create credentials:** `python -m cli llm creds-create < creds.json`
   See `references/credentials.md` for provider-specific formats (API_KEY, AWS, AZURE, GCP).
2. **Validate:** `python -m cli llm creds-validate ID --provider PROVIDER --model MODEL`
3. **Create LLM config:** `python -m cli llm create < config.json` referencing the credential ID. See `references/providers.md` for provider model details.

## Data Source Management

- `python -m cli datasource list` / `python -m cli datasource get ID` / `python -m cli datasource create` / `python -m cli datasource update ID` / `python -m cli datasource delete ID`
- Note: connector setup, MDE, and QLI configuration require the Alation web UI.

## Common Mistakes

**Mistake:** Copying a data product's full spec into the agent prompt to "teach" it about the data.
Why it seems reasonable: the agent needs to know what data is available.
Instead: Set `data_product_id` as a `fixed` parameter binding on the agent's tools. The tools will fetch the product context at runtime. See `references/bindings.md` pattern 1.

**Mistake:** Creating a new SMTP tool when one already exists.
Why it seems reasonable: the user asked to send email.
Instead: Run `python -m cli tool list` first. Look for existing tools with `tool_type: "SMTP"`.

**Mistake:** Asking the user for an API token or credentials during agent/tool creation.
Why it seems reasonable: auth might seem like a per-operation concern.
Instead: Authentication is handled automatically by credentials.local. If auth fails, direct the user to the `setup` skill.

## Next Steps

After finishing configuration, suggest next steps to the user — but don't proceed without their go-ahead unless their original request already implies it.

- **After creating an agent or tool:** Share the `url` from the CLI response so the user can view it in the Alation UI.
- **After creating an agent:** Always offer to test it by sending a message via the **ask** skill. Then suggest scheduling it with the **automate** skill if relevant.
- **After creating a tool:** Suggest adding it to an agent (using this skill) or wiring it into a workflow (using the **automate** skill).

## Red Flags
- "I'll add the product schema to the agent's system prompt" — use parameter bindings instead.
- "I need to create an SMTP tool" — check if one exists first.
- "What's your API token?" — credentials come from credentials.local, not the user.

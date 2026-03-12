---
name: automate
description: "Use when the user wants to create, run, schedule, or debug automated workflows and recurring jobs. Triggers: create workflow, schedule report, automate query, run flow, send me a daily/weekly email, cron schedule, recurring report, debug workflow, flow not running, execution stuck, schedule not triggering, execute workflow, run this every day/week/month, set up recurring, automate this. Key signal: any mention of recurring, scheduled, daily, weekly, or automated execution means this skill, not ask. Not for one-time queries — use ask. Not for creating agents or tools — use configure."
---

# Automate

Create, manage, and debug automated workflows and schedules.

## Routing

| User Intent | CLI Command |
|---|---|
| List workflows | `python -m cli workflow list` |
| Create a workflow | `python -m cli workflow create` or `python -m cli workflow create --from-template NAME` |
| Run a workflow | `python -m cli workflow execute ID [--dry-run]` |
| Schedule a workflow | `python -m cli schedule create` |
| Enable/disable schedule | `python -m cli schedule enable ID` / `python -m cli schedule disable ID` |
| Debug a failing workflow | See Diagnostics section below |

## Not This Skill

- User wants to **run a one-time query** → use `ask`
- User wants to **create an agent or tool** needed by a workflow → use `configure`
- User wants to **create a data product** that a workflow will query → use `curate`

Key distinction: "Set up a daily email report" is `automate`. "Set up an agent" is `configure`. The word "set up" alone is ambiguous — look for scheduling/recurring/automation language to choose `automate`.

## Creating Workflows

### Step 0: Verify the query works first

Before building a flow, make sure the underlying query or task works interactively. Use the **ask** skill to run it once — if the query fails or the agent gives bad results, fix that before automating it. Debugging a broken query inside a scheduled flow is much harder than
testing it interactively.

### Step 1: Look up the agent

Before building a flow, identify which agent it should use. Both default agents (by ref name) and custom agents (by UUID) work in flows.

Use the **configure** skill's agent commands to look up agents:
```bash
# List all agents — look for the one that matches the user's intent
python -m cli agent list

# Get a specific agent's config, including its input_json_schema
python -m cli agent get <agent_uuid>
```

The agent's `input_json_schema` tells you exactly what inputs the flow node needs. This matters because different agents require different inputs — a custom agent might need `project_name` and `report_type`, not just `message` and `data_product_id`.

If the user has been working with a specific custom agent (e.g., they just created or configured one), use that agent's UUID — don't substitute a default agent.

### Step 2: Build the flow from a template or from scratch

Three templates are available — list with `python -m cli workflow templates`:

1. **agent-only** — Run a single agent. The simplest flow — good for running any agent on a schedule.
   Required: `name`, `agent_id`, `query`

2. **query-and-email** — Query a data product, email the results.
   Required: `name`, `agent_id`, `data_product_id`, `query`, `tool_id` (SMTP), `email`, `subject`

3. **query-only** — Query a data product (no email).
   Required: `name`, `agent_id`, `data_product_id`, `query`

Example: `python -m cli workflow create --from-template agent-only --agent-id <uuid> --query "Generate the weekly summary"`

If the agent needs additional inputs beyond `message` (check `input_json_schema`), build the flow JSON from scratch instead. See `references/agent-schemas.md` for how to wire agent inputs into flow nodes — it covers both default and custom agents.

## Scheduling

```bash
python -m cli schedule create \
  --workflow-id <uuid> \
  --name "Weekly sales report" \
  --cron "0 9 * * 1" \
  --timezone "America/Los_Angeles" \
  --timeout 60
```

- Cron format: `minute hour day month weekday` (e.g., `0 9 * * 1` = Monday 9am)
- Minimum interval: 60 minutes
- `--timezone` defaults to `America/Los_Angeles`
- `--timeout` defaults to 60 minutes
- `--disabled` creates the schedule in disabled state (useful for testing)
- Auth is handled automatically — the CLI finds the user's managed auth config
- To manage existing schedules: `python -m cli schedule list/get/enable/disable/delete`

## Diagnostics

When a workflow or schedule isn't working, diagnose using the CLI:

1. **Schedule not firing?**
   - `python -m cli schedule get <id>` — check `enabled` and `next_run_at`
   - If disabled, enable with `python -m cli schedule enable <id>`
   - If `next_run_at` is in the past, the scheduler may be stalled — escalate to the user's admin

2. **Execution failing?**
   - `python -m cli workflow list` — check recent execution status
   - Auth errors → use the **setup** skill to re-authenticate
   - Tool/agent not found → verify IDs with `python -m cli tool list` / `python -m cli agent list`

3. **Issues beyond CLI access** (stuck executions, duplicate runs, scheduler pod health) require admin/SRE intervention. Describe the symptoms to the user and suggest they contact their Alation administrator.

## Common Mistakes

**Mistake:** Creating a new SMTP tool when the user asks to email results.
Why it seems reasonable: the flow needs an email tool.
Instead: List existing tools first (`python -m cli tool list`). There is likely already an SMTP tool configured. Only create a new one if none exists.

**Mistake:** Using a default agent when the user has a custom agent for the task.
Why it seems reasonable: default agents are easier to reference.
Instead: If the user created or configured a custom agent, use its UUID. Check `python -m cli agent list` to find the right one. Look up its `input_json_schema` to know what inputs the flow node needs.

**Mistake:** Hardcoding agent/tool IDs in the flow definition without verifying they exist.
Why it seems reasonable: the user provided the names.
Instead: Look up IDs using `python -m cli agent list` or `python -m cli tool list`.

**Mistake:** Building a flow without checking what inputs the agent expects.
Why it seems reasonable: most agents just need `message`.
Instead: Run `python -m cli agent get <uuid>` and check `input_json_schema`. Custom agents often need additional inputs like `data_product_id` or domain-specific parameters.

## Sharing URLs

After creating a workflow, share the `url` from the CLI response so the user can view it in the Alation UI. Schedule responses include a `workflow_url` pointing to the parent workflow.

## Red Flags
- "I'll create an SMTP tool for this workflow" — check existing tools first.
- "Let me build the flow JSON from scratch" — try templates first.

# Agent Chat Workflow

Detailed workflow for chatting with Alation AI agents via `scripts/run-cli chat`.

## Agent Selection

### Common Default Agents

These are frequently used defaults. There may be other default or custom agents better suited to the task — run `scripts/run-cli agent list` to see everything available.

| Agent | Use When |
|-------|----------|
| `sql_query_agent` | Help writing or refining SQL queries (requires `data_product_id`) |
| `catalog_search_agent` | Search and understand catalog assets |
| `deep_research_agent` | Multi-step data research with context |
| `charting_agent` | Interactive chart creation |
| `data_product_query_agent` | Query data products with automatic discovery |
| `alamigo_agent` | General help questions about the Alation product (not for data queries) |

### Custom Agents

Custom agents are referenced by their UUID (config ID) instead of a ref name. To discover custom agents:
```bash
scripts/run-cli agent list
```

Then use the agent's `id` field wherever you would use a default agent ref.

## Step 1: Check Agent Schema

```bash
# Default agent
scripts/run-cli agent get-default <agent_ref>

# Custom agent
scripts/run-cli agent get <agent_config_id>
```

This fetches the agent's configuration from the server, including its parameters and tools.

## Step 2: Start Conversation

```bash
# Default agent
echo '{"message": "<user question>"}' | scripts/run-cli chat send <agent_ref>

# Custom agent (by UUID)
echo '{"message": "<user question>"}' | scripts/run-cli chat send <agent_config_id>
```

For agents that require additional parameters (e.g., `sql_query_agent` needs `data_product_id`):
```bash
echo '{"message": "Show me top customers", "data_product_id": "<id>"}' | scripts/run-cli chat send sql_query_agent
```

## Step 3: Handle Streaming Output

The chat command streams SSE events. Output includes:
- **text** parts: The agent's response text
- **thinking** parts: The agent's reasoning (shown as preview)
- **tool-call** parts: Tools the agent wants to invoke
- **tool-return** parts: Results from tool invocations

## Step 4: Continue Conversation

To send a follow-up message in the same chat:
```bash
echo '{"message": "Now filter by region"}' | scripts/run-cli chat send <agent_ref> --chat-id <uuid>
```

## Step 5: Handle Pending Tool Approvals

If the agent requests tool approval, the stream output will indicate pending tools. Use the chat_id to continue after approval.

## Chat Management

```bash
# Get messages from a chat
scripts/run-cli chat messages <chat_id>

# Cancel a running chat
scripts/run-cli chat cancel <chat_id>

# List recent chats
scripts/run-cli chat history --limit 10
```

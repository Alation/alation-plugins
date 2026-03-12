# Alation Plugin

AI coding agent plugin for the Alation platform. Query data products, explore catalogs, automate workflows, curate metadata, and configure AI agents — all through natural language.

## Prerequisites

- Python 3.10+
- An Alation instance with OAuth client registration (see Step 2 below)

## Getting Started

### Step 1: Install the Plugin

#### Claude Code
Register the marketplace:
```
/plugin marketplace add Alation/alation-plugins
```
Install the plugin:
```
/plugin install alation@alation-plugins
```

#### Claude Cowork
1. Go to "Customize" in the sidebar.
2. Click "Browse plugins" to open up the modal.
3. Go to the "Personal" tab.
4. Hit the "+" button and add marketplace by URL.

#### Other Platforms (Codex, Gemini, etc.)
The plugin works on other platforms, but setup is manual for now — automatic installation on these platforms doesn't include the CLI that skills depend on. Clone this repo and ensure the full `cli/` directory is available alongside `skills/`. First-class support is on the way; watch this repo for updates.

### Step 2: Register an OAuth Client

The plugin uses OAuth to connect to your Alation instance. You (or an admin of your instance) will need to register an OAuth client if one doesn't exist already.

1. Follow the instructions in [these docs](https://alation.github.io/agent-studio-docs/guides/authentication/user-initiated-auth/).
2. Set the "Client Type" to `public`.
3. Add `http://127.0.0.1:18722/callback` as an allowed redirect URL.
4. Save the **client ID** — you'll need it in the next step.

### Step 3: Authenticate

Ask your agent to set up the Alation plugin. It will prompt you for:

- **Base URL** — your instance URL, e.g. `https://your-alation-instance.alationcloud.com`
- **Client ID** — from Step 2

After that, it will open a browser window for you to log in.

> **Cowork users:** The redirect page after login will not load. This is expected. Copy the full URL from that page and paste it back into the chat so Claude can finish authentication.

## Usage Examples

Once you're set up, just ask in natural language. Here are some things you can try:

```
What marketing data do we have?
```
```
Search the catalog for anything related to "customer orders"
```
```
What was our total revenue last quarter?
```
```
Create an agent that can answer questions about our finance data
```
```
Send me a summary of last week's sales every Monday
```
```
Add a descriptions to the customer orders data product
```

## Skills

| Skill | What it does |
|-------|-------------|
| **ask** | Query data products, chat with AI agents, invoke tools |
| **explore** | Search and browse the data catalog, data products, and marketplaces |
| **configure** | Create and manage agents, tools, LLMs, and data source connections |
| **automate** | Build, run, and schedule recurring workflows |
| **curate** | Manage data products, publish to marketplaces, enrich catalog metadata |
| **setup** | Configure credentials and authenticate with your Alation instance |

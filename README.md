# Alation Plugin

AI coding agent plugin for the Alation platform. Query data products, explore catalogs, automate workflows, curate metadata, and configure AI agents — all through natural language.

The latest plugin is always available from the [Releases](https://github.com/Alation/alation-plugins/releases/latest) page.

## Prerequisites

- Python 3.10+
- An Alation instance with OAuth client registration (see Step 2 below)

## Getting Started

### Step 1: Install the Plugin

#### Claude Code

Register the marketplace and install:
```
/plugin marketplace add Alation/alation-plugins
/plugin install alation@alation-plugins
```

#### Claude Cowork
##### Marketplace
1. Go to "Customize" in the sidebar.
2. Click the "+" icon next to "Personal Plugins" and select "Add marketplace"
3. Add marketplace by URL: `https://github.com/Alation/alation-plugins`
4. Install `Alation`

> _Note: After adding a marketplace, you can check for updates or re-install plugins by clicking the "+" icon next to "Personal Plugins" and selecting "Browse Plugins", then navigating to the "Personal" tab and selecting the `alation-plugins` marketplace_

##### Zip File
1. Download `alation.zip` from the [latest release](https://github.com/Alation/alation-plugins/releases/latest).
2. Go to **Customize** in the sidebar.
3. Click the "+" icon next to "Presonal Plugins" and select "Upload plugin"
4. Drag and drop or browse files to the downloaded zip file to install

#### Codex / Gemini CLI

Install skills using the agent skills installer:

```bash
curl -fsSL https://raw.githubusercontent.com/Alation/alation-plugins/main/bin/install-agent-skills.sh | bash -s -- --scope user
```

This installs portable agent skills to `~/.agents/skills/`, which both Codex and Gemini CLI read automatically.
Each skill bundles the Alation CLI — no separate installation needed.

To install to the current project only:
```bash
curl -fsSL https://raw.githubusercontent.com/Alation/alation-plugins/main/bin/install-agent-skills.sh | bash -s -- --scope workspace
```

#### Other Platforms

Any agent that supports the [Agent Skills](https://agentskills.io) format can use Alation skills.
Run the install script above with `--scope user` or `--scope workspace` and point your agent at the resulting `.agents/skills/` directory.

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

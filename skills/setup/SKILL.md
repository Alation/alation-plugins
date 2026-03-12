---
name: setup
description: Guide the user through creating and validating their credentials.local file for connecting to Alation. Covers local development, Cowork, and container environments.
---

# Setup

Guide the user through creating and validating their `credentials.local` file.

## Behavior Contract
- Be direct and concise.
- Ask only for information needed for the current step.
- Ask for credential fields in one grouped message (not one-by-one).
- Do not guess user values, do not prefill URLs, and do not present extra options during field collection.
- Do not echo secrets (password, client secret, auth code) back to the user.
- Always execute `setup check` first and after any change.

## Routing

| Task | CLI Command |
|---|---|
| Check if setup is complete | `python -m cli setup check` |
| Save credentials to file | `python -m cli setup credentials --base_url <URL> ...` |
| Log in via OAuth (local) | `python -m cli setup login` |
| Log in via OAuth (Cowork/container) | `python -m cli setup login --cowork` |
| Complete Cowork OAuth with redirect URL | `python -m cli setup login --cowork --code "<URL>"` |


## Process

### 1. Run `setup check`

```bash
python -m cli setup check
```

This returns JSON with five sections: `credentials_file`, `token`, `api`, `environment`, and `ready`.

Evaluate in this order (first match wins):
- If `ready: true` -> setup is complete, go to step 6.
- If `credentials_file.found: false` -> go to step 2.
- If `credentials_file.auth_method` is null → go to step 3
- If `credentials_file.auth_method: "oauth"` and `token.found: false` -> go to step 4.
- If `credentials_file.auth_method: "oauth"` and `token.expired: true` -> go to step 4.
- If `api.authenticated: false` -> go to step 5.
- Otherwise, return to step 1.

### 2. Choose Auth Method

Ask the user which authentication method to use once:

- **OAuth (recommended):** Browser-based login using Authorization Code + PKCE. Requires an OAuth client registered in Alation with redirect URI `http://127.0.0.1:18722/callback`.
- **Username/password (legacy):** Django session login with email and password.

### 3. Create credentials.local

Ask the user for their values in a single message. Do not present options, guesses, or prefilled URLs — just ask directly for what's needed.

**OAuth** — ask for: `base_url`, `client_id`, and `client_secret` (note client_secret is optional for public clients).

**Username/password** — ask for: `base_url`, `username`, and `password`.

Run the credentials command with the values provided:

**OAuth:**
```bash
python -m cli setup credentials --base_url <URL> --client_id <ID> --client_secret <SECRET>
```

Or, if there's no client secret:

```bash
python -m cli setup credentials --base_url <URL> --client_id <ID>
```

**Username/password:**
```bash
python -m cli setup credentials --base_url <URL> --username <USER> --password <PASS>
```

If you ever notice SSL errors or a self-signed certificate, with user approval, add `--disable_ssl_verification`. You must get user approval for this.

The command outputs JSON with `{"status": "ok", "path": "..."}` on success. If there's a `base_url_mismatch` error, then request approval from the user to re-run with `--force` which will overwrite the existing credentials.

On success, return to step 1 to check the setup again.

### 4. Complete OAuth Login

Use this step only for OAuth-based setup when token is missing/expired.

Check `environment.container` from the step 1 `setup check` output to determine which flow to use.

**Local environment** (not in Cowork/container):

```bash
python -m cli setup login
```

This opens a browser window for the user to log in. On success, prints the check result as JSON.

**Cowork/container environment** — use the `--cowork` flag for a two-step manual flow:

Step 1 — start the flow:
```bash
python -m cli setup login --cowork
```

This returns JSON with `status: "pending"` and an `auth_url` field. Show the `auth_url` to the user and ask them to complete login in browser. Clearly and concisely explain that the user will need to copy the redirect URL from their browser back into the chat.

Step 2 — the user visits the URL in their browser, authorizes, and gets redirected to a page that fails to load. They paste the full redirect URL into chat. Complete the flow:
```bash
python -m cli setup login --cowork --code "<REDIRECT_URL>"
```

The `--code` flag accepts either a bare authorization code or a full redirect URL (e.g., `http://127.0.0.1:18722/callback?code=ABC&state=XYZ`).

On success, return to step 1 to check the setup again.

**Note:** An Alation admin must register `http://127.0.0.1:18722/callback` as an allowed redirect URI for the OAuth client.

### 5. Diagnose Authentication Failure

If `api.authenticated: false`, check the `api.error` field and:
- **Token expired:** Re-run `setup login` (step 4)
- **Wrong credentials:** Ask the user to verify their credentials and recreate (step 3)
- **Server unreachable** (`api.reachable: false`): Ask the user to verify `base_url`, VPN, or network connectivity
- **SSL errors:** Re-run step 3 with `--disable_ssl_verification` after explicit user approval.

### 6. Confirm

When `ready: true`, tell the user setup is complete. If the user has no clear intent beyond setup, then suggest 2-3 things they could try, drawn from the examples below. Pick what's most relevant to anything the user has mentioned so far. If you have no signal, default to the first two.

Example suggestions (adapt, don't recite):
- "Want to see what data sources are available? I can browse the catalog for you."
- "Have a data question? Tell me what you're looking for and I'll query it."
- "Need to set up an AI agent or connect a new tool? I can walk you through that."
- "Want to create or manage a data product? I can help with that."
- "Have a recurring report or query to automate? I can set up a scheduled workflow."

## Not This Skill
- User wants to **create or manage agents, tools, or LLMs** → use `configure`
- User wants to **add a data source connection** → use `configure`
- User wants to **browse the catalog** → use `explore`
- User wants to **query data** → use `ask`
- User is already authenticated and wants to **do something** → route to the appropriate skill

## Common Mistakes
**Mistake:** Running `setup login` before credentials exist.
Why it seems reasonable: the user said "log me in."
Instead: Always run `setup check` first. If no credentials file exists, go to step 2.

**Mistake:** Using `--cowork` in a local environment, or omitting it in a container.
Why it seems reasonable: the user didn't specify their environment.
Instead: Check `environment.container` from `setup check`. Use `--cowork` only when `container: true`.

**Mistake:** Guessing or prefilling the user's base URL, client ID, or credentials.
Why it seems reasonable: you might infer the URL from context.
Instead: Always ask. Credentials must come directly from the user.

**Mistake:** Re-prompting for all credentials when only one value is wrong.
Why it seems reasonable: starting fresh feels safer.
Instead: Ask for just the corrected value and re-run `setup credentials` with all values.

## Red Flags
- "Let me try connecting to the API directly" — always use the CLI, never raw API calls.
- "I'll use a default client ID" — there is no default. Ask the user.
- "Let me set up your agent" — that's `configure`, not `setup`.

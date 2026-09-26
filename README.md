# Research Site + Playwright + Browser Use MCP Orchestrator

This package replaces the previous **Jev** agent layer with **Browser Use**.
It is designed for an authorized Reddit-like website that you own/control.

## Architecture

```text
MCP client / AI agent
        |
        v
Python MCP server
        |
        +--> account manager / scheduler / state
        |
        +--> Playwright (owns browser + contexts + storage state)
                 |
        +--------+--------+
        |        |        |
       A01      A02      A03
     Context  Context  Context
        |        |        |
        +--------+--------+
                 |
                 v
          Browser Use Agent
          (CDP connection)
                 |
                 v
           Your website
```

### Why this arrangement

Playwright remains the application owner of the browser process, isolated
`BrowserContext`s, login state, and lifecycle. Browser Use connects to the
already-running Playwright-owned Chromium instance over CDP and supplies the
agentic browser decisions. Browser Use's current API supports a `BrowserSession`
with a `cdp_url`, and its `Agent` accepts a `browser_session`. The Browser Use
project also documents Playwright/CDP integration. 

This means you do **not** need Jev or its `TYPESAFE_API_KEY`.

## Browser Use version

The ZIP pins `browser-use==0.13.10`, which requires `mcp==2.1.1`. It also pins
Playwright to `1.63.0` because this project explicitly uses Playwright for the
browser/context lifecycle. Browser Use 0.13.10 was released on September 4,
2026. 

## Dependency note

Browser Use 0.13.10 requires `mcp==2.1.1`. MCP SDK v2 renamed the old
`FastMCP` server class to `MCPServer`, so this project intentionally uses:

```python
from mcp.server.mcpserver import MCPServer
```

Do **not** install the old `mcp<2` / `mcp.server.fastmcp` combination in this
environment; it conflicts with Browser Use 0.13.10.

The project also installs Playwright explicitly because Playwright is the
application-owned browser/context layer in this architecture.

## LLM configuration

Browser Use still needs an LLM provider. The default configuration is:

```json
"browser_use": {
  "package": "browser-use==0.13.10",
  "llm": {
    "provider": "openai",
    "model": "gpt-4.1-mini"
  }
}
```

Set the corresponding environment variable before starting the MCP server:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
```

Other supported choices can be configured without changing the orchestrator:

```json
"provider": "google",
"model": "gemini-3-flash-preview"
```

```powershell
$env:GOOGLE_API_KEY="YOUR_KEY"
```

or:

```json
"provider": "anthropic",
"model": "claude-sonnet-4-6"
```

```powershell
$env:ANTHROPIC_API_KEY="YOUR_KEY"
```

Browser Use also supports its own `ChatBrowserUse` gateway with
`BROWSER_USE_API_KEY`; see its current model documentation for the available
providers and models.

## Install on Windows

You already have Node installed, but this version no longer needs Node for the
browser-agent layer.

```powershell
cd C:\path\to\research_site_browser_use_mcp
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Then test the Python packages:

```powershell
python -c "import browser_use, playwright; from mcp.server.mcpserver import MCPServer; print('Browser Use + Playwright + MCP v2 OK')"
```

## Configure the website

Edit `config/settings.json`:

```json
{
  "site": {
    "base_url": "http://localhost:3000",
    "community_paths": ["/r/technology", "/r/programming"]
  }
}
```

Use only the URL/routes of your authorized development site.

## Account profiles

```text
profiles/
├── account_01/
│   └── state.json
├── account_02/
│   └── state.json
└── account_03/
    └── state.json
```

Each account is opened in a separate Playwright `BrowserContext` and receives
its own storage state.

Example `config/accounts.json`:

```json
{
  "accounts": [
    {
      "id": "account_01",
      "profile_dir": "profiles/account_01",
      "state_file": "state.json",
      "enabled": true
    }
  ]
}
```

## Login/bootstrap

The MCP tool:

```text
bootstrap_account("account_01")
```

opens the configured site in a visible Playwright browser, waits 30 seconds for
you to complete normal login, then saves the Playwright storage state.

Treat `profiles/*/state.json` as credentials. Never commit or share them.

## MCP tools

- `health_check`
- `bootstrap_account(account_id)`
- `run_account_workflow(account_id)`
- `run_all_accounts()`

Example MCP client configuration:

```json
{
  "mcpServers": {
    "research-site-browser-use": {
      "command": "C:\\path\\to\\research_site_browser_use_mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\research_site_browser_use_mcp\\run_server.py"
      ]
    }
  }
}
```

## Workflow behavior

The starter workflow is still **discovery-only**. It asks Browser Use to find
candidate posts and return visible IDs/titles/URLs. It does not submit replies,
vote, follow, delete, or otherwise change content.

The application controls:

- account isolation
- account rotation
- per-account workload limit
- interval scheduling
- outer execution timeout
- persistent state/logging
- start/stop lifecycle

Browser Use controls the agentic page interaction inside the already-open
Playwright browser.

### Important limitation

The package cannot safely invent your site's selectors or success conditions.
Once your own site's DOM/API is known, deterministic application-level checks
can be added for:

- stable post IDs (`data-post-id` or API IDs)
- duplicate detection
- reply box and submit locators
- successful-submission verification
- exact per-account counters

## About the other repository in your screenshot: Vercel `agent-browser`

The screenshot is the **Vercel Labs `agent-browser`** repository, not Browser
Use. It is a separate Rust/Node browser-automation CLI. Its current docs expose
an MCP server (`agent-browser mcp`) and session/profile/state tooling, and it
uses Chrome/Chromium through CDP rather than Playwright/Puppeteer as its core
CLI dependency.

That project is interesting if you want a CLI-first browser tool or a direct
MCP browser server. For this ZIP, however, **Browser Use is the selected agent
layer**, because your request was specifically to replace Jev with Browser Use
while keeping the Python MCP/orchestrator architecture.

Do not install both Browser Use and agent-browser unless you have a specific
reason to maintain two independent agent layers.

## Security boundary

This project is for automation on a site you own/control. It intentionally
contains no anti-bot bypass, CAPTCHA circumvention, stealth/evasion logic, or
third-party platform enforcement avoidance.

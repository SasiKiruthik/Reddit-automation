from __future__ import annotations

import json
from pathlib import Path
from mcp.server.mcpserver import MCPServer
from .workflow import Workflow

mcp = MCPServer("research-site-browser-use-automation")
ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@mcp.tool()
async def health_check() -> dict:
    """Return configuration and environment information without exposing secrets."""
    settings = load_json("config/settings.json")
    return {
        "name": "research-site-browser-use-automation",
        "base_url": settings["site"]["base_url"],
        "posts_per_account": settings["workflow"]["posts_per_account"],
        "interval_seconds": settings["workflow"]["interval_seconds"],
        "browser": "Playwright-owned contexts + Browser Use over CDP",
        "browser_use": settings["browser_use"]["package"],
        "llm_provider": settings["browser_use"]["llm"]["provider"],
    }


@mcp.tool()
async def bootstrap_account(account_id: str) -> dict:
    """Open the site's login page visibly and persist the account storage state."""
    settings = load_json("config/settings.json")
    accounts = load_json("config/accounts.json")["accounts"]
    matches = [a for a in accounts if a["id"] == account_id and a.get("enabled", True)]
    if not matches:
        return {"ok": False, "error": f"Unknown or disabled account: {account_id}"}
    result = await Workflow(settings, matches).bootstrap_account(matches[0])
    return {"ok": bool(result.get("ok")), "result": result}


@mcp.tool()
async def run_account_workflow(account_id: str) -> dict:
    """Run the bounded, non-submitting research workflow for one account."""
    settings = load_json("config/settings.json")
    accounts = load_json("config/accounts.json")["accounts"]
    matches = [a for a in accounts if a["id"] == account_id and a.get("enabled", True)]
    if not matches:
        return {"ok": False, "error": f"Unknown or disabled account: {account_id}"}
    result = await Workflow(settings, matches).run_account(matches[0])
    return {"ok": True, "result": result}


@mcp.tool()
async def run_all_accounts() -> dict:
    """Rotate through all enabled accounts with isolated Playwright contexts."""
    settings = load_json("config/settings.json")
    accounts = load_json("config/accounts.json")["accounts"]
    results = await Workflow(settings, accounts).run_all()
    return {"ok": True, "results": results}


if __name__ == "__main__":
    mcp.run(transport="stdio")

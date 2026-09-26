from __future__ import annotations

import asyncio
from .browser_use_runner import BrowserUseRunner
from .state import StateStore


class Workflow:
    """Application-owned account rotation and bounded Browser Use workflow."""

    def __init__(self, settings: dict, accounts: list[dict]):
        self.settings = settings
        self.accounts = accounts
        self.state = StateStore()
        self.browser_use = BrowserUseRunner(settings)

    async def bootstrap_account(self, account: dict) -> dict:
        base = self.settings["site"]["base_url"].rstrip("/")
        result = await self.browser_use.bootstrap_account(account, base, wait_seconds=30)
        self.state.add_run({
            "account_id": account["id"],
            "phase": "bootstrap",
            "result": result,
        })
        return result

    async def run_account(self, account: dict) -> dict:
        wf = self.settings["workflow"]
        base = self.settings["site"]["base_url"].rstrip("/")
        paths = self.settings["site"].get("community_paths") or ["/"]

        results = []
        discovered = 0
        for path in paths:
            if discovered >= wf["posts_per_account"]:
                break

            start_url = base + "/" + path.lstrip("/")
            remaining = wf["posts_per_account"] - discovered
            task = f"""
You are operating ONLY on the authorized research website at {base}.
Open {start_url}. Find up to {remaining} eligible posts for a research test.
Do not submit, delete, vote, follow, or otherwise change content.
Return a compact JSON array in your final response with id, title and url when
those values are visible. Skip posts that appear already processed by this account.
Stop when you have found {remaining} candidates or when none remain.
"""
            result = await self.browser_use.run(
                account,
                task,
                start_url=start_url,
                max_steps=wf["max_steps_per_post"],
                max_seconds=wf["max_seconds_per_post"],
            )
            results.append({"phase": "discovery", "community": path, "result": result})
            discovered += 1

            if discovered < wf["posts_per_account"]:
                await asyncio.sleep(wf["interval_seconds"])

        self.state.add_run({"account_id": account["id"], "results": results})
        return {"account_id": account["id"], "results": results}

    async def run_all(self) -> list[dict]:
        out = []
        for account in self.accounts:
            if not account.get("enabled", True):
                continue
            out.append(await self.run_account(account))
        return out

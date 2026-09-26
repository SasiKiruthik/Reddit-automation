from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright


class BrowserUseRunner:
    """Run Browser Use against a Playwright-owned browser/context.

    Playwright owns the Chromium process, BrowserContext, storage state, and
    lifecycle. Browser Use connects to that already-running browser over CDP
    and supplies the agentic decision layer.
    """

    def __init__(self, settings: dict, root: Path | None = None):
        self.settings = settings
        self.root = root or Path(__file__).resolve().parents[1]

    @staticmethod
    def _free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _profile_paths(self, account: dict) -> tuple[Path, Path]:
        profile_dir = self.root / account.get("profile_dir", f"profiles/{account['id']}")
        profile_dir.mkdir(parents=True, exist_ok=True)
        state_path = profile_dir / account.get("state_file", "state.json")
        return profile_dir, state_path

    def _make_llm(self):
        from browser_use import (
            ChatAnthropic,
            ChatBrowserUse,
            ChatGoogle,
            ChatOpenAI,
        )

        cfg = self.settings.get("browser_use", {}).get("llm", {})
        provider = cfg.get("provider", "openai").lower()
        model = cfg.get("model")

        if provider == "browser_use":
            return ChatBrowserUse(model=model or "bu-2-0")
        if provider == "google":
            return ChatGoogle(model=model or "gemini-3-flash-preview")
        if provider == "anthropic":
            return ChatAnthropic(model=model or "claude-sonnet-4-6", temperature=0.0)
        if provider == "openai":
            return ChatOpenAI(model=model or "gpt-4.1-mini")
        raise ValueError(f"Unsupported browser_use.llm.provider: {provider}")

    async def _run_agent_on_page(
        self,
        *,
        page,
        task: str,
        max_steps: int,
        max_seconds: int,
        cdp_url: str,
    ) -> Any:
        from browser_use import Agent, BrowserSession, BrowserProfile

        profile = BrowserProfile(
            cdp_url=cdp_url,
            is_local=True,
            keep_alive=True,
            headless=self.settings.get("workflow", {}).get("headless", False),
        )
        session = BrowserSession(browser_profile=profile)
        llm = self._make_llm()

        # The CDP connection sees the Playwright-created context/page. We first
        # navigate with Playwright, then tell Browser Use to operate only there.
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=session,
            max_steps=max_steps,
            use_vision=False,
        )
        history = await agent.run(max_steps=max_steps)

        final_result = None
        if hasattr(history, "final_result"):
            final_result = history.final_result()
        else:
            final_result = str(history)

        # Agent.run() honors keep_alive=True and therefore does not kill the
        # Playwright-owned browser. Playwright remains responsible for saving
        # storage state and closing the context/browser below.
        return {
            "final_result": final_result,
            "history": str(history),
            "url": page.url,
            "title": await page.title(),
        }

    async def bootstrap_account(
        self, account: dict, start_url: str, wait_seconds: int = 30
    ) -> dict:
        _, state_path = self._profile_paths(account)
        port = self._free_port()

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=False,
                args=[f"--remote-debugging-port={port}"],
            )
            try:
                context_options = {}
                if state_path.exists():
                    context_options["storage_state"] = str(state_path)
                context = await browser.new_context(**context_options)
                page = await context.new_page()
                await page.goto(start_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(wait_seconds * 1000)
                await context.storage_state(path=str(state_path))
                return {
                    "ok": True,
                    "action": "bootstrap",
                    "account_id": account["id"],
                    "state_path": str(state_path),
                    "url": page.url,
                    "title": await page.title(),
                }
            finally:
                await browser.close()

    async def run(
        self,
        account: dict,
        task: str,
        start_url: str | None = None,
        max_steps: int = 20,
        max_seconds: int = 90,
    ) -> dict:
        _, state_path = self._profile_paths(account)
        port = self._free_port()

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=self.settings.get("workflow", {}).get("headless", False),
                args=[f"--remote-debugging-port={port}"],
            )
            context = None
            try:
                context_options = {}
                if state_path.exists():
                    context_options["storage_state"] = str(state_path)
                context = await browser.new_context(**context_options)
                page = await context.new_page()
                if start_url:
                    await page.goto(start_url, wait_until="domcontentloaded")

                # Browser Use has its own time/step controls. The outer Python
                # timeout is an additional hard stop for the application.
                result = await asyncio.wait_for(
                    self._run_agent_on_page(
                        page=page,
                        task=task,
                        max_steps=max_steps,
                        max_seconds=max_seconds,
                        cdp_url=f"http://127.0.0.1:{port}",
                    ),
                    timeout=max_seconds + 30,
                )

                await context.storage_state(path=str(state_path))
                result.update({
                    "ok": True,
                    "account_id": account["id"],
                    "state_path": str(state_path),
                })
                return result
            except asyncio.TimeoutError:
                return {
                    "ok": False,
                    "account_id": account["id"],
                    "error": f"Outer workflow timeout after {max_seconds + 30}s",
                }
            finally:
                if context:
                    await context.close()
                await browser.close()

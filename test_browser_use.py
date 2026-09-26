import asyncio
import os

from browser_use import Agent, BrowserSession, ChatGoogle
from browser_use.browser import BrowserProfile


async def main():
    print("Starting Browser Use test...", flush=True)

    site_url = os.getenv("TEST_SITE_URL", "http://localhost:3000")

    print(f"Target website: {site_url}", flush=True)

    # Browser Use starts/owns the Chromium session for this test.
    browser_session = BrowserSession(
        browser_profile=BrowserProfile(
            headless=False,
        )
    )

    print("Browser session created.", flush=True)

    agent = Agent(
        task=f"""
        Open this website:

        {site_url}

        Do not click buttons, submit forms, log in, or modify anything.

        Simply inspect the current webpage and report:
        1. The page title
        2. The current URL
        3. A short description of the visible content
        """,
        llm=ChatGoogle(model="gemini-3.8-flash"),
        browser_session=browser_session,
    )

    print("Starting Browser Use agent...", flush=True)

    result = await agent.run()

    print("\n" + "=" * 60, flush=True)
    print("BROWSER USE RESULT", flush=True)
    print("=" * 60, flush=True)
    print(result, flush=True)

    await browser_session.kill()

    print("\nBrowser closed.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
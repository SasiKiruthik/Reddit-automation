import asyncio

from browser_use import Agent, BrowserSession, ChatGoogle

from config import (
    get_enabled_accounts,
    get_base_url,
    get_community_url,
)


MODEL = "gemini-3.8-flash"


def build_task(account, base_url):

    community_url = get_community_url(account)

    username = account["username"]
    password = account["password"]

    posts_to_reply = account["workload"]["posts_to_reply"]

    return f"""
You are operating ONLY on this local Reddit-style website:

{base_url}

Do not visit any external website.

Account information:

Username:
{username}

Password:
{password}

Target community:

{community_url}

Required number of replies:

{posts_to_reply}

Perform the following workflow on the LOCAL website:

1. Open the website:

   {base_url}

2. Log in using the supplied username and password.

3. Verify that login was successful.

4. Navigate to:

   {community_url}

5. Inspect the available posts.

6. Select suitable posts according to the configured workload.

7. Open the selected post.

8. Read the post content.

9. Generate a short, natural and relevant reply using Gemini.

10. Enter the generated reply into the reply/comment field.

11. Verify that the entered text is correct.

12. Submit the reply.

13. Verify that the reply appears successfully on the page.

Important restrictions:

- Only use the local website.
- Do not visit Reddit.com or any other external website.
- Do not create new posts.
- Do not modify existing posts.
- Do not change account settings.
- Do not perform unrelated actions.
- Do not submit duplicate replies.
- Only process the configured number of posts.

At the end, report:

- Account ID
- Username
- Login status
- Community
- Number of posts processed
- Generated replies
- Submission status
- Any errors encountered
"""


async def run_account(account, base_url):

    account_id = account["id"]

    print()
    print("-" * 70)
    print(f"Starting account: {account_id}")
    print("-" * 70)

    print(f"Username : {account['username']}")
    print(f"Community: {account['community']['name']}")
    print(f"URL      : {get_community_url(account)}")

    session = None

    try:

        session = BrowserSession()

        llm = ChatGoogle(
            model=MODEL
        )

        task = build_task(
            account,
            base_url
        )

        agent = Agent(
            task=task,
            llm=llm,
            browser_session=session,
        )

        result = await agent.run()

        print()
        print(f"Account {account_id} completed.")
        print()
        print(result)

    except Exception as error:

        print()
        print(
            f"Account {account_id} failed:"
        )
        print(error)

    finally:

        if session is not None:

            try:
                await session.kill()

            except Exception:
                pass


async def run_all_accounts(config):

    accounts = get_enabled_accounts(config)

    base_url = get_base_url(config)

    if not accounts:
        print("No enabled accounts found.")
        return

    print(
        f"Processing {len(accounts)} enabled account(s)."
    )

    for index, account in enumerate(accounts):

        await run_account(
            account,
            base_url
        )

        # Delay between accounts.
        if index < len(accounts) - 1:

            delay = account.get(
                "workload",
                {}
            ).get(
                "delay_between_replies_seconds",
                0
            )

            if delay > 0:

                print()
                print(
                    f"Waiting {delay} seconds "
                    f"before next account..."
                )

                await asyncio.sleep(delay)
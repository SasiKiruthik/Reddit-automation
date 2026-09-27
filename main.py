import asyncio

from config import (
    load_config,
    validate_config,
    get_enabled_accounts,
    get_base_url,
    get_community_url,
)

from account_runner import run_all_accounts


async def main():

    print()
    print("=" * 70)
    print("LOCAL REDDIT-STYLE RESEARCH AUTOMATION")
    print("=" * 70)

    # -------------------------
    # LOAD CONFIG
    # -------------------------

    config = load_config()

    # -------------------------
    # VALIDATE CONFIG
    # -------------------------

    validate_config(config)

    # -------------------------
    # GET CONFIGURED VALUES
    # -------------------------

    accounts = get_enabled_accounts(config)
    base_url = get_base_url(config)

    print()
    print(f"Website         : {base_url}")
    print(f"Enabled accounts: {len(accounts)}")
    print()

    # -------------------------
    # DISPLAY ACCOUNTS
    # -------------------------

    for account in accounts:

        community_url = get_community_url(account)

        print(
            f"- {account['id']} "
            f"→ {account['community']['name']} "
            f"→ {community_url}"
        )

    print()

    # -------------------------
    # RUN ACCOUNTS
    # -------------------------

    await run_all_accounts(config)

    print()
    print("=" * 70)
    print("ALL CONFIGURED ACCOUNTS PROCESSED")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
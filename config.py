import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "config" / "accounts.json"


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found:\n{CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_enabled_accounts(config):
    return [
        account
        for account in config.get("accounts", [])
        if account.get("enabled", True)
    ]


def get_base_url(config):
    return config["site"]["base_url"].rstrip("/")


def get_community_url(account):
    return account["community"]["url"].rstrip("/")


def validate_config(config):

    # -------------------------
    # SITE
    # -------------------------

    if "site" not in config:
        raise ValueError(
            "Missing 'site' in config/accounts.json."
        )

    if not config["site"].get("base_url"):
        raise ValueError(
            "Missing 'site.base_url' in config/accounts.json."
        )

    # -------------------------
    # ACCOUNTS
    # -------------------------

    accounts = config.get("accounts", [])

    if not accounts:
        raise ValueError(
            "No accounts configured."
        )

    for account in accounts:

        account_id = account.get("id", "unknown")

        if not account.get("username"):
            raise ValueError(
                f"Account {account_id} is missing username."
            )

        if not account.get("password"):
            raise ValueError(
                f"Account {account_id} is missing password."
            )

        # -------------------------
        # COMMUNITY
        # -------------------------

        community = account.get("community")

        if not community:
            raise ValueError(
                f"Account {account_id} is missing community."
            )

        if not community.get("name"):
            raise ValueError(
                f"Account {account_id} is missing community.name."
            )

        # IMPORTANT:
        # accounts.json uses community.url
        if not community.get("url"):
            raise ValueError(
                f"Account {account_id} is missing community.url."
            )

        # -------------------------
        # WORKLOAD
        # -------------------------

        workload = account.get("workload", {})

        if "posts_to_reply" not in workload:
            raise ValueError(
                f"Account {account_id} is missing "
                "workload.posts_to_reply."
            )

        if "delay_between_replies_seconds" not in workload:
            raise ValueError(
                f"Account {account_id} is missing "
                "workload.delay_between_replies_seconds."
            )

    # -------------------------
    # COMMENTING
    # -------------------------

    commenting = config.get("commenting", {})

    if not isinstance(commenting, dict):
        raise ValueError(
            "'commenting' must be an object."
        )

    return True
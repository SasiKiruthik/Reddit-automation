from __future__ import annotations

def generate_reply(post: dict, settings: dict) -> str:
    cfg = settings.get("reply", {})
    if cfg.get("mode", "template") == "template":
        return cfg.get("template", "Interesting post. Thanks for sharing this perspective.")
    raise ValueError("Only template mode is included in this starter package.")

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

class StateStore:
    def __init__(self, path: str = "data/state.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"processed_posts": {}, "runs": []}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass

    def processed(self, account_id: str, post_id: str) -> bool:
        return post_id in self.data.get("processed_posts", {}).get(account_id, [])

    def mark_processed(self, account_id: str, post_id: str):
        self.data.setdefault("processed_posts", {}).setdefault(account_id, [])
        if post_id not in self.data["processed_posts"][account_id]:
            self.data["processed_posts"][account_id].append(post_id)
        self.save()

    def add_run(self, record: dict):
        record = dict(record)
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.data.setdefault("runs", []).append(record)
        self.data["runs"] = self.data["runs"][-200:]
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

import json
from typing import Any, Dict


class JsonSerializer:
    """
    简单的 JSON 存档器，读写字典结构。
    """

    def save(self, snapshot: Dict[str, Any], path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

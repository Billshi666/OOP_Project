from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Seat:
    """
    表示一方的“对弈参与者”配置：
    - human: 人类玩家（可游客或已登录）
    - ai: AI 玩家（按等级区分）
    """

    kind: str  # "human" | "ai"
    ai_level: Optional[int] = None
    username: Optional[str] = None

    def display_name(self) -> str:
        if self.kind == "ai":
            return f"AI{self.ai_level or 1}"
        return self.username or "Guest"

from __future__ import annotations

from typing import Optional

from src.core.player import PlayerColor
from src.game.base_game import Game, GameConfig
from src.rules.othello_rule import OthelloRuleEngine


class OthelloGame(Game):
    def __init__(self, default_size: int = 8):
        super().__init__(default_size=default_size, rule_engine=OthelloRuleEngine(), name="othello")

    def start(self, config: Optional[GameConfig] = None) -> None:
        super().start(config)
        self._place_initial_discs()

    def _place_initial_discs(self) -> None:
        mid = self.board.size // 2
        # 标准开局：白白对角、黑黑对角
        self.board.set(mid - 1, mid - 1, PlayerColor.WHITE)
        self.board.set(mid, mid, PlayerColor.WHITE)
        self.board.set(mid - 1, mid, PlayerColor.BLACK)
        self.board.set(mid, mid - 1, PlayerColor.BLACK)

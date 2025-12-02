from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.board import Board
from src.core.history import History
from src.core.move import Move
from src.core.player import PlayerColor


@dataclass
class GameResult:
    winner: Optional[PlayerColor]  # None means draw
    message: str


@dataclass
class ApplyResult:
    ended: bool
    message: str = ""
    result: Optional[GameResult] = None


class RuleEngine:
    """
    规则策略接口。
    """

    def is_legal(self, board: Board, move: Move, history: History) -> bool:
        raise NotImplementedError

    def apply_move(self, board: Board, move: Move, history: History) -> ApplyResult:
        raise NotImplementedError

    def is_end(self, board: Board, history: History) -> bool:
        raise NotImplementedError

    def result(self, board: Board, history: History) -> GameResult:
        raise NotImplementedError

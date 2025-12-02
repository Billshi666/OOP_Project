from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .player import PlayerColor


@dataclass
class Move:
    x: int
    y: int
    color: Optional[PlayerColor]
    is_pass: bool = False

    @staticmethod
    def pass_move(color: PlayerColor) -> "Move":
        return Move(x=-1, y=-1, color=color, is_pass=True)

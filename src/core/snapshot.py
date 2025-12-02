from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .player import PlayerColor


@dataclass
class GameSnapshot:
    size: int
    board: List[List[Optional[str]]]  # "B"/"W"/None
    to_move: Optional[PlayerColor]
    ended: bool
    message: str = ""
    result: Optional[str] = None  # e.g., "Black wins"

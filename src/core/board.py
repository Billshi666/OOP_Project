from __future__ import annotations

import copy
from typing import List, Optional, Tuple

from .player import PlayerColor


class Board:
    """
    棋盘负责维护格子状态和基本操作，不参与规则判定。
    """

    def __init__(self, size: int):
        if size < 1:
            raise ValueError("Board size must be positive")
        self.size = size
        self.cells: List[List[Optional[PlayerColor]]] = [
            [None for _ in range(size)] for _ in range(size)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x: int, y: int) -> Optional[PlayerColor]:
        return self.cells[y][x]

    def set(self, x: int, y: int, color: Optional[PlayerColor]) -> None:
        self.cells[y][x] = color

    def is_empty(self, x: int, y: int) -> bool:
        return self.get(x, y) is None

    def neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        # 上下左右相邻点
        deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        return [(x + dx, y + dy) for dx, dy in deltas if self.in_bounds(x + dx, y + dy)]

    def clone(self) -> "Board":
        # 深拷贝棋盘，用于快照
        return copy.deepcopy(self)

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .board import Board
from .player import PlayerColor


@dataclass
class Memento:
    board_snapshot: Board
    to_move: PlayerColor


class History:
    """
    维护悔棋/存档所需的快照栈。
    """

    def __init__(self):
        self.stack: List[Memento] = []

    def push(self, board: Board, to_move: PlayerColor) -> None:
        self.stack.append(Memento(board_snapshot=board.clone(), to_move=to_move))

    def pop(self) -> Memento:
        if not self.stack:
            raise IndexError("No history to undo")
        return self.stack.pop()

    def can_undo(self) -> bool:
        return len(self.stack) > 0

    def to_serializable(self):
        """
        转为可序列化的结构，包含每步的棋盘状态和待行棋方。
        """
        return [
            {
                "to_move": m.to_move.value,
                "board": [[cell.value if cell else None for cell in row] for row in m.board_snapshot.cells],
            }
            for m in self.stack
        ]

    @staticmethod
    def from_serializable(data, size: int) -> "History":
        """
        从序列化数据重建快照栈。
        """
        history = History()
        for entry in data:
            board = Board(size)
            for y, row in enumerate(entry["board"]):
                for x, cell in enumerate(row):
                    if cell is None:
                        board.set(x, y, None)
                    else:
                        board.set(x, y, PlayerColor(cell))
            history.stack.append(Memento(board_snapshot=board, to_move=PlayerColor(entry["to_move"])))
        return history

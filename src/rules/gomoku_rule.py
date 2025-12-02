from __future__ import annotations

from typing import List, Tuple

from src.core.board import Board
from src.core.history import History
from src.core.move import Move
from src.core.player import PlayerColor
from src.rules.base_rule import RuleEngine, ApplyResult, GameResult


class GomokuRuleEngine(RuleEngine):
    """
    五子棋规则：禁止 pass，先连五者胜，满盘平局。
    """

    def is_legal(self, board: Board, move: Move, history: History) -> bool:
        if move.is_pass:
            return False
        return board.in_bounds(move.x, move.y) and board.is_empty(move.x, move.y)

    def apply_move(self, board: Board, move: Move, history: History) -> ApplyResult:
        board.set(move.x, move.y, move.color)
        if self._is_win(board, move.x, move.y, move.color):
            result = GameResult(winner=move.color, message=f"{move.color.name} wins by five in a row")
            return ApplyResult(ended=True, message=result.message, result=result)
        if self._is_board_full(board):
            result = GameResult(winner=None, message="Draw: board is full")
            return ApplyResult(ended=True, message=result.message, result=result)
        return ApplyResult(ended=False, message=f"Move ({move.x},{move.y})")

    def is_end(self, board: Board, history: History) -> bool:
        # 胜负在 apply_move 中已判断；此处只需检测满盘
        return self._is_board_full(board)

    def result(self, board: Board, history: History) -> GameResult:
        # 仅在满盘平局时调用
        return GameResult(winner=None, message="Draw: board is full")

    # 内部工具
    def _is_board_full(self, board: Board) -> bool:
        return all(cell is not None for row in board.cells for cell in row)

    def _is_win(self, board: Board, x: int, y: int, color: PlayerColor) -> bool:
        directions: List[Tuple[int, int]] = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            count += self._count_dir(board, x, y, dx, dy, color)
            count += self._count_dir(board, x, y, -dx, -dy, color)
            if count >= 5:
                return True
        return False

    def _count_dir(self, board: Board, x: int, y: int, dx: int, dy: int, color: PlayerColor) -> int:
        cx, cy = x + dx, y + dy
        count = 0
        while board.in_bounds(cx, cy) and board.get(cx, cy) == color:
            count += 1
            cx += dx
            cy += dy
        return count

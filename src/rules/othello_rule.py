from __future__ import annotations

from typing import List, Tuple

from src.core.board import Board
from src.core.history import History
from src.core.move import Move
from src.core.player import PlayerColor
from src.rules.base_rule import ApplyResult, GameResult, RuleEngine


class OthelloRuleEngine(RuleEngine):
    """
    黑白棋（Othello/Reversi）规则：
    - 只能落子在能翻转至少一个对手棋子的空位；
    - 若当前方无任何合法落子，则该回合被迫弃权（pass）；
    - 棋盘满或双方都无合法落子时终局，按棋子数判胜负。
    """

    def __init__(self) -> None:
        self.last_error_message: str = ""

    def is_legal(self, board: Board, move: Move, history: History) -> bool:
        if move.color is None:
            self.last_error_message = "Missing player color"
            return False

        if move.is_pass:
            if self.legal_moves(board, move.color):
                self.last_error_message = "Pass not allowed: you have legal moves"
                return False
            self.last_error_message = ""
            return True

        if not board.in_bounds(move.x, move.y) or not board.is_empty(move.x, move.y):
            self.last_error_message = ""
            return False

        flips = self.flips_for_move(board, move.x, move.y, move.color)
        if not flips:
            self.last_error_message = "Illegal move in Othello: must flip at least one disc"
            return False
        self.last_error_message = ""
        return True

    def apply_move(self, board: Board, move: Move, history: History) -> ApplyResult:
        if move.color is None:
            return ApplyResult(ended=False, message="Missing player color")

        if move.is_pass:
            return ApplyResult(ended=False, message="Forced pass (no legal moves)")

        flips = self.flips_for_move(board, move.x, move.y, move.color)
        board.set(move.x, move.y, move.color)
        for fx, fy in flips:
            board.set(fx, fy, move.color)
        return ApplyResult(ended=False, message=f"Move ({move.x},{move.y}); flipped {len(flips)}")

    def is_end(self, board: Board, history: History) -> bool:
        if self._is_board_full(board):
            return True
        # 双方都无合法落子才终局
        return (not self.legal_moves(board, PlayerColor.BLACK)) and (not self.legal_moves(board, PlayerColor.WHITE))

    def result(self, board: Board, history: History) -> GameResult:
        black, white = self.count_discs(board)
        if black > white:
            return GameResult(winner=PlayerColor.BLACK, message=f"Black wins {black} vs {white}")
        if white > black:
            return GameResult(winner=PlayerColor.WHITE, message=f"White wins {white} vs {black}")
        return GameResult(winner=None, message=f"Draw {black} : {white}")

    # --- Othello helpers (public) ---

    def legal_moves(self, board: Board, color: PlayerColor) -> List[Tuple[int, int]]:
        moves: List[Tuple[int, int]] = []
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y) and self.flips_for_move(board, x, y, color):
                    moves.append((x, y))
        return moves

    def flips_for_move(self, board: Board, x: int, y: int, color: PlayerColor) -> List[Tuple[int, int]]:
        if not board.in_bounds(x, y) or not board.is_empty(x, y):
            return []

        opponent = color.opposite()
        flips: List[Tuple[int, int]] = []
        directions = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]
        for dx, dy in directions:
            flips.extend(self._ray_flips(board, x, y, color, opponent, dx, dy))
        return flips

    def count_discs(self, board: Board) -> Tuple[int, int]:
        black = 0
        white = 0
        for row in board.cells:
            for cell in row:
                if cell == PlayerColor.BLACK:
                    black += 1
                elif cell == PlayerColor.WHITE:
                    white += 1
        return black, white

    # --- internals ---

    def _is_board_full(self, board: Board) -> bool:
        return all(cell is not None for row in board.cells for cell in row)

    def _ray_flips(
        self,
        board: Board,
        x: int,
        y: int,
        color: PlayerColor,
        opponent: PlayerColor,
        dx: int,
        dy: int,
    ) -> List[Tuple[int, int]]:
        cx, cy = x + dx, y + dy
        ray: List[Tuple[int, int]] = []

        # 第一格必须是对方棋子
        if not board.in_bounds(cx, cy) or board.get(cx, cy) != opponent:
            return []

        while board.in_bounds(cx, cy):
            cell = board.get(cx, cy)
            if cell == opponent:
                ray.append((cx, cy))
            elif cell == color:
                return ray  # 被己方棋子封口，合法翻转
            else:
                break  # 遇到空位，不能翻转
            cx += dx
            cy += dy
        return []

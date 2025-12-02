from __future__ import annotations

from collections import deque
from typing import List, Optional, Set, Tuple

from src.core.board import Board
from src.core.history import History
from src.core.move import Move
from src.core.player import PlayerColor
from src.rules.base_rule import RuleEngine, ApplyResult, GameResult


class GoRuleEngine(RuleEngine):
    """
    简化的围棋规则：支持提子、pass、数子计分，不考虑劫与自杀禁手。
    """

    def is_legal(self, board: Board, move: Move, history: History) -> bool:
        if move.is_pass:
            return True
        if not board.in_bounds(move.x, move.y):
            return False
        if not board.is_empty(move.x, move.y):
            return False
        # 不考虑自杀禁手，故不检测落子后气
        return True

    def apply_move(self, board: Board, move: Move, history: History) -> ApplyResult:
        if move.is_pass:
            return ApplyResult(ended=False, message="Pass")

        board.set(move.x, move.y, move.color)
        captured = 0

        # 尝试提取对方无气的链
        for nx, ny in board.neighbors(move.x, move.y):
            neighbor_color = board.get(nx, ny)
            if neighbor_color is None or neighbor_color == move.color:
                continue
            chain, liberties = self._collect_chain(board, nx, ny)
            if liberties == 0:
                for cx, cy in chain:
                    board.set(cx, cy, None)
                captured += len(chain)

        message = f"Move ({move.x},{move.y}); captured {captured}"
        return ApplyResult(ended=False, message=message)

    def is_end(self, board: Board, history: History) -> bool:
        # 预防极端情况：棋盘满视为结束
        for row in board.cells:
            for cell in row:
                if cell is None:
                    return False
        return True

    def result(self, board: Board, history: History) -> GameResult:
        black_score, white_score = self._score(board)
        if black_score > white_score:
            return GameResult(winner=PlayerColor.BLACK, message=f"Black wins {black_score} vs {white_score}")
        if white_score > black_score:
            return GameResult(winner=PlayerColor.WHITE, message=f"White wins {white_score} vs {black_score}")
        return GameResult(winner=None, message=f"Draw {black_score} : {white_score}")

    # 内部工具
    def _collect_chain(self, board: Board, x: int, y: int) -> Tuple[Set[Tuple[int, int]], int]:
        color = board.get(x, y)
        visited: Set[Tuple[int, int]] = set()
        liberties = 0
        queue = deque([(x, y)])
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            for nx, ny in board.neighbors(cx, cy):
                neighbor = board.get(nx, ny)
                if neighbor is None:
                    liberties += 1
                elif neighbor == color and (nx, ny) not in visited:
                    queue.append((nx, ny))
        return visited, liberties

    def _score(self, board: Board) -> Tuple[int, int]:
        black = 0
        white = 0
        size = board.size
        visited = [[False] * size for _ in range(size)]

        # 先加上盘面实子
        for y in range(size):
            for x in range(size):
                stone = board.get(x, y)
                if stone == PlayerColor.BLACK:
                    black += 1
                elif stone == PlayerColor.WHITE:
                    white += 1

        # 计算空地归属
        for y in range(size):
            for x in range(size):
                if visited[y][x]:
                    continue
                if board.get(x, y) is not None:
                    continue
                region, owners = self._empty_region_owner(board, x, y, visited)
                if len(owners) == 1:
                    owner = owners.pop()
                    if owner == PlayerColor.BLACK:
                        black += region
                    elif owner == PlayerColor.WHITE:
                        white += region
        return black, white

    def _empty_region_owner(
        self, board: Board, x: int, y: int, visited: List[List[bool]]
    ) -> Tuple[int, Set[PlayerColor]]:
        queue = deque([(x, y)])
        visited[y][x] = True
        count = 0
        owners: Set[PlayerColor] = set()
        while queue:
            cx, cy = queue.popleft()
            count += 1
            for nx, ny in board.neighbors(cx, cy):
                if board.get(nx, ny) is None and not visited[ny][nx]:
                    visited[ny][nx] = True
                    queue.append((nx, ny))
                else:
                    neighbor = board.get(nx, ny)
                    if neighbor is not None:
                        owners.add(neighbor)
        return count, owners

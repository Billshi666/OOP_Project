from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.core.board import Board
from src.core.move import Move
from src.core.player import PlayerColor
from src.rules.othello_rule import OthelloRuleEngine


@dataclass(frozen=True)
class ScoredMove:
    x: int
    y: int
    score: float
    flips: int


def choose_othello_move(
    level: int,
    board: Board,
    color: PlayerColor,
    engine: OthelloRuleEngine,
    rng: Optional[random.Random] = None,
) -> Move:
    rng = rng or random.Random()
    legal = engine.legal_moves(board, color)
    if not legal:
        return Move.pass_move(color)

    if level <= 1:
        x, y = rng.choice(legal)
        return Move(x=x, y=y, color=color, is_pass=False)

    scored: List[ScoredMove] = []
    for x, y in legal:
        flips = engine.flips_for_move(board, x, y, color)
        sim = board.clone()
        sim.set(x, y, color)
        for fx, fy in flips:
            sim.set(fx, fy, color)
        score = _score_position(board, sim, x, y, color, engine, flips=len(flips))
        scored.append(ScoredMove(x=x, y=y, score=score, flips=len(flips)))

    best_score = max(m.score for m in scored)
    best = [m for m in scored if m.score == best_score]
    chosen = rng.choice(best)
    return Move(x=chosen.x, y=chosen.y, color=color, is_pass=False)


def _score_position(
    before: Board,
    after: Board,
    x: int,
    y: int,
    color: PlayerColor,
    engine: OthelloRuleEngine,
    flips: int,
) -> float:
    size = before.size
    opponent = color.opposite()

    # 位置权重：角 > 边 > 内部；临近空角则极大惩罚
    positional = _positional_weight(before, x, y)

    # 走完后的子力差（越大越好）
    black, white = engine.count_discs(after)
    my_count = black if color == PlayerColor.BLACK else white
    opp_count = white if color == PlayerColor.BLACK else black
    disc_diff = my_count - opp_count

    # 限制对手行动力（越少越好）
    opp_mobility = len(engine.legal_moves(after, opponent))

    # 组合评分（经验权重，目标：稳定胜过随机 AI）
    score = 0.0
    score += positional * 100.0
    score += flips * 2.0
    score += disc_diff * 1.0
    score -= opp_mobility * 5.0

    # 尺寸越大，边角更重要
    score *= 8.0 / float(size)

    return score


def _positional_weight(board: Board, x: int, y: int) -> int:
    size = board.size
    corners = {(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)}
    if (x, y) in corners:
        return 100

    # “危险区”：角附近 3 个位置，且该角仍为空时
    for cx, cy, danger in _corner_danger_zones(size):
        if (x, y) in danger and board.get(cx, cy) is None:
            return -50

    # 边线略好，内部默认
    if x == 0 or y == 0 or x == size - 1 or y == size - 1:
        return 10
    return 1


def _corner_danger_zones(size: int) -> List[Tuple[int, int, List[Tuple[int, int]]]]:
    return [
        (0, 0, [(0, 1), (1, 0), (1, 1)]),
        (0, size - 1, [(0, size - 2), (1, size - 1), (1, size - 2)]),
        (size - 1, 0, [(size - 2, 0), (size - 1, 1), (size - 2, 1)]),
        (
            size - 1,
            size - 1,
            [(size - 2, size - 1), (size - 1, size - 2), (size - 2, size - 2)],
        ),
    ]

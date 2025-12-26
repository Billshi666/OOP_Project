from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.board import Board
from src.core.history import History
from src.core.move import Move
from src.core.player import PlayerColor
from src.core.snapshot import GameSnapshot
from src.rules.base_rule import RuleEngine, ApplyResult, GameResult
from src.serializer import JsonSerializer


@dataclass
class GameConfig:
    size: int


class Game:
    """
    模板基类：包含通用的生命周期与流程控制，具体规则交给 RuleEngine。
    """

    def __init__(self, default_size: int, rule_engine: RuleEngine, name: str):
        self.default_size = default_size
        self.rule_engine = rule_engine
        self.name = name
        self.serializer = JsonSerializer()

        self.board: Board = Board(default_size)
        self.history = History()
        self.to_move: PlayerColor = PlayerColor.BLACK
        self.ended: bool = False
        self.last_result: Optional[GameResult] = None
        self.consecutive_passes: int = 0  # 围棋用

    def start(self, config: Optional[GameConfig] = None) -> None:
        size = config.size if config else self.default_size
        self.board = Board(size)
        self.history = History()
        self.to_move = PlayerColor.BLACK
        self.ended = False
        self.last_result = None
        self.consecutive_passes = 0

    def play_move(self, move: Move) -> ApplyResult:
        if self.ended:
            return ApplyResult(ended=True, message="Game already ended", result=self.last_result)
        if not move.is_pass and not self.board.in_bounds(move.x, move.y):
            return ApplyResult(ended=False, message="Move out of bounds")
        if not move.is_pass and not self.board.is_empty(move.x, move.y):
            return ApplyResult(ended=False, message="Position already occupied")
        if not self.rule_engine.is_legal(self.board, move, self.history):
            # 允许规则引擎提供更具体的错误信息（例如自杀禁手）
            message = getattr(self.rule_engine, "last_error_message", "Illegal move by rule")
            return ApplyResult(ended=False, message=message)

        # 保存当前局面以支持悔棋
        self.history.push(self.board, self.to_move)

        result = self.rule_engine.apply_move(self.board, move, self.history)

        # pass 计数只对围棋有用；其他游戏视为不允许 pass
        if move.is_pass:
            self.consecutive_passes += 1
        else:
            self.consecutive_passes = 0

        # 行棋方轮换（若已结束可以不轮换）
        if not result.ended:
            self.to_move = self.to_move.opposite()

        # 如果规则引擎未宣布结束，检查终局条件
        if not result.ended and self.rule_engine.is_end(self.board, self.history):
            result.ended = True
            result.result = self.rule_engine.result(self.board, self.history)

        # 双 pass 作为围棋终局条件
        if not result.ended and self.consecutive_passes >= 2:
            result.ended = True
            result.result = self.rule_engine.result(self.board, self.history)

        self.ended = result.ended
        self.last_result = result.result

        return result

    def pass_move(self) -> ApplyResult:
        # 统一入口创建 pass move
        move = Move.pass_move(self.to_move)
        return self.play_move(move)

    def undo(self) -> ApplyResult:
        if not self.history.can_undo():
            return ApplyResult(ended=self.ended, message="No move to undo")
        memento = self.history.pop()
        self.board = memento.board_snapshot
        self.to_move = memento.to_move
        self.ended = False
        self.last_result = None
        self.consecutive_passes = 0
        return ApplyResult(ended=self.ended, message="Undone")

    def resign(self) -> ApplyResult:
        if self.ended:
            return ApplyResult(ended=True, message="Game already ended", result=self.last_result)
        winner = self.to_move.opposite()
        result = GameResult(winner=winner, message=f"{winner.name} wins by resignation")
        self.ended = True
        self.last_result = result
        return ApplyResult(ended=True, message=result.message, result=result)

    def restart(self, config: Optional[GameConfig] = None) -> None:
        self.start(config)

    def save(self, path: str, meta: Optional[dict] = None) -> None:
        snapshot = self._build_snapshot(include_history=True)
        if meta:
            snapshot["meta"] = meta
        self.serializer.save(snapshot, path)

    def load(self, path: str) -> None:
        snapshot = self.serializer.load(path)
        self._load_snapshot(snapshot)

    def get_snapshot(self) -> GameSnapshot:
        return self._build_snapshot(include_history=False)

    # 内部方法
    def _build_snapshot(self, include_history: bool) -> dict:
        return {
            "game": self.name,
            "size": self.board.size,
            "board": [[cell.value if cell else None for cell in row] for row in self.board.cells],
            "to_move": self.to_move.value,
            "ended": self.ended,
            "history": self.history.to_serializable() if include_history else [],
            "last_result": self.last_result.winner.value if self.last_result and self.last_result.winner else None,
            "last_result_msg": self.last_result.message if self.last_result else "",
        }

    def _load_snapshot(self, data: dict) -> None:
        size = data["size"]
        self.board = Board(size)
        for y, row in enumerate(data["board"]):
            for x, cell in enumerate(row):
                self.board.set(x, y, PlayerColor(cell) if cell else None)
        self.to_move = PlayerColor(data["to_move"])
        self.ended = data.get("ended", False)
        winner_value = data.get("last_result")
        last_msg = data.get("last_result_msg", "")
        if winner_value:
            self.last_result = GameResult(winner=PlayerColor(winner_value), message=last_msg)
        elif self.ended and last_msg:
            # Draw or ended-with-message cases store winner as None in snapshot
            self.last_result = GameResult(winner=None, message=last_msg)
        else:
            self.last_result = None
        self.history = History.from_serializable(data.get("history", []), size)
        self.consecutive_passes = 0  # 存档恢复后重新统计 pass

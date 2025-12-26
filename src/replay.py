from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.core.player import PlayerColor


@dataclass
class ReplayState:
    board: List[List[Optional[str]]]  # "B"/"W"/None
    to_move: str  # "B"/"W"


class ReplaySession:
    """
    回放会话：基于存档中的 history + 当前局面构建时间线。

    timeline 规则（兼容旧存档）：
    - history[i] 保存的是“第 i+1 手落子前”的局面（Game.play_move 里 push 的 memento）；
    - 最后追加当前 board，形成 len(history)+1 个状态。
    """

    def __init__(self, save_data: Dict[str, Any]) -> None:
        self.save_data = save_data
        self.game: str = str(save_data.get("game", "unknown"))
        self.meta: Dict[str, Any] = dict(save_data.get("meta") or {})

        self.timeline: List[ReplayState] = self._build_timeline(save_data)
        self.index: int = 0

    def next(self) -> None:
        if self.index < len(self.timeline) - 1:
            self.index += 1

    def prev(self) -> None:
        if self.index > 0:
            self.index -= 1

    def jump(self, idx: int) -> None:
        if not self.timeline:
            self.index = 0
            return
        self.index = max(0, min(idx, len(self.timeline) - 1))

    def current_snapshot(self) -> Dict[str, Any]:
        state = self.timeline[self.index]
        snapshot: Dict[str, Any] = {
            "mode": "replay",
            "game": self.game,
            "size": len(state.board),
            "board": state.board,
            "to_move": state.to_move,
            "ended": self._is_last(),
            "last_result": self.save_data.get("last_result"),
            "last_result_msg": self.save_data.get("last_result_msg", ""),
        }
        players = self.meta.get("players")
        if isinstance(players, dict):
            snapshot["players"] = players
        else:
            snapshot["players"] = {
                PlayerColor.BLACK.value: {"label": "Guest"},
                PlayerColor.WHITE.value: {"label": "Guest"},
            }
        return snapshot

    def current_message(self) -> str:
        total = max(0, len(self.timeline) - 1)
        if self.index == 0:
            return f"Replay {self.game} 0/{total}: start"

        prev = self.timeline[self.index - 1]
        cur = self.timeline[self.index]

        mover = prev.to_move
        mover_side = "Black" if mover == PlayerColor.BLACK.value else "White"
        mover_label = self._player_label(mover)
        mover_text = f"{mover_side}({mover_label})" if mover_label else mover_side

        action = _describe_transition(self.game, prev.board, cur.board, mover)
        suffix = " (end)" if self._is_last() else ""
        return f"Replay {self.game} {self.index}/{total}: {mover_text} {action}{suffix}"

    # --- internals ---

    def _is_last(self) -> bool:
        return self.index == len(self.timeline) - 1 and bool(self.save_data.get("ended", False))

    def _build_timeline(self, data: Dict[str, Any]) -> List[ReplayState]:
        history = data.get("history") or []
        timeline: List[ReplayState] = []

        if isinstance(history, list):
            for entry in history:
                if not isinstance(entry, dict):
                    continue
                board = entry.get("board")
                to_move = entry.get("to_move")
                if isinstance(board, list) and to_move in (PlayerColor.BLACK.value, PlayerColor.WHITE.value):
                    timeline.append(ReplayState(board=board, to_move=to_move))

        # 当前局面作为最后一帧
        board = data.get("board")
        to_move = data.get("to_move")
        if isinstance(board, list) and to_move in (PlayerColor.BLACK.value, PlayerColor.WHITE.value):
            timeline.append(ReplayState(board=board, to_move=to_move))

        # 若存档没有 history，也没有 board，则退化为一个空 timeline
        return timeline

    def _player_label(self, color_value: str) -> str:
        players = self.meta.get("players")
        if not isinstance(players, dict):
            return ""
        entry = players.get(color_value)
        if not isinstance(entry, dict):
            return ""
        label = entry.get("label")
        if isinstance(label, str) and label and label != "Guest":
            return label
        if entry.get("kind") == "ai" and isinstance(label, str):
            return label
        return ""


def _describe_transition(game: str, prev: List[List[Optional[str]]], cur: List[List[Optional[str]]], mover: str) -> str:
    if _boards_equal(prev, cur):
        return "Pass"

    size = len(prev)
    added: List[Tuple[int, int]] = []
    removed: List[Tuple[int, int]] = []
    changed: List[Tuple[int, int]] = []

    for y in range(size):
        for x in range(size):
            a = prev[y][x]
            b = cur[y][x]
            if a == b:
                continue
            changed.append((x, y))
            if a is None and b is not None:
                added.append((x, y))
            elif a is not None and b is None:
                removed.append((x, y))

    move_part = ""
    if len(added) == 1:
        x, y = added[0]
        move_part = f"Move ({x},{y})"
    else:
        move_part = "Move"

    # 额外信息：Othello 翻转数 / Go 提子数
    if game == "othello":
        flips = 0
        for x, y in changed:
            if prev[y][x] is None:
                continue
            if cur[y][x] == mover and prev[y][x] != mover:
                flips += 1
        return f"{move_part}; flipped {flips}"

    captures = len(removed)
    if captures:
        return f"{move_part}; captured {captures}"
    return move_part


def _boards_equal(a: List[List[Optional[str]]], b: List[List[Optional[str]]]) -> bool:
    if len(a) != len(b):
        return False
    for row_a, row_b in zip(a, b):
        if row_a != row_b:
            return False
    return True

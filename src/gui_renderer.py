from __future__ import annotations

from typing import Dict, List, Optional

import tkinter as tk

from src.core.player import PlayerColor


class GuiRenderer:
    """
    GUI 渲染器：根据游戏快照刷新棋盘按钮和状态标签。

    说明：
    - 控制器仍然调用 render(snapshot, message)，只是由本类更新 Tk 控件，而不是在控制台打印。
    - 不修改原有控制器/游戏逻辑，只是替换渲染实现。
    """

    def __init__(
        self,
        board_buttons: List[List[tk.Button]],
        info_label: tk.Label,
        result_label: tk.Label,
        turn_label: tk.Label,
        players_label: Optional[tk.Label] = None,
    ) -> None:
        self.board_buttons = board_buttons
        self.info_label = info_label
        self.result_label = result_label
        self.turn_label = turn_label
        self.players_label = players_label

        # 记录默认按钮背景色，便于在“合法点高亮”后恢复
        self._default_btn_bg: Optional[str] = None

    def render(self, snapshot: Dict, message: Optional[str] = "") -> None:
        """
        根据当前快照刷新棋盘和状态信息。
        snapshot 的结构与原有 Game.get_snapshot() 返回的一致。
        """
        size: int = snapshot["size"]
        board: List[List[Optional[str]]] = snapshot["board"]
        to_move = snapshot.get("to_move")
        ended: bool = snapshot.get("ended", False)
        last_result = snapshot.get("last_result")
        last_result_msg: str = snapshot.get("last_result_msg", "")
        players = snapshot.get("players") or {}

        show_legal_moves = bool(snapshot.get("show_legal_moves", False))
        legal_moves = snapshot.get("legal_moves") or []
        legal_set = {tuple(m) for m in legal_moves} if show_legal_moves else set()

        # 更新棋盘按钮：只在 0..size-1 范围内启用并显示棋子，其余禁用清空
        max_size = len(self.board_buttons)
        for y in range(max_size):
            for x in range(max_size):
                btn = self.board_buttons[y][x]
                if self._default_btn_bg is None:
                    try:
                        self._default_btn_bg = btn.cget("bg")
                    except Exception:
                        self._default_btn_bg = None
                if x < size and y < size:
                    cell = board[y][x]
                    if cell == PlayerColor.BLACK.value:
                        text = "●"
                        bg = self._default_btn_bg
                    elif cell == PlayerColor.WHITE.value:
                        text = "○"
                        bg = self._default_btn_bg
                    else:
                        if (x, y) in legal_set:
                            text = "*"
                            bg = "#b7f0b1"  # light green
                        else:
                            text = "+"
                            bg = self._default_btn_bg
                    if bg is not None:
                        btn.configure(text=text, state=tk.NORMAL, bg=bg)
                    else:
                        btn.configure(text=text, state=tk.NORMAL)
                else:
                    btn.configure(text="", state=tk.DISABLED)

        # 信息提示
        self.info_label.config(text=message or "")

        # 玩家信息
        if self.players_label is not None:
            black_entry = players.get(PlayerColor.BLACK.value) or {}
            white_entry = players.get(PlayerColor.WHITE.value) or {}
            self.players_label.config(
                text=f"Players: Black={_format_player(black_entry)} | White={_format_player(white_entry)}"
            )

        # 结果与轮次
        if ended:
            self.result_label.config(text=last_result_msg or "Game ended")
            self.turn_label.config(text="")
        else:
            self.result_label.config(text="")
            if to_move:
                player = "Black" if to_move == PlayerColor.BLACK.value else "White"
                entry = players.get(to_move) or {}
                label = entry.get("label")
                suffix = f" ({label})" if isinstance(label, str) and label and label != "Guest" else ""
                self.turn_label.config(text=f"{player}{suffix} to move")
            else:
                self.turn_label.config(text="")

    def render_message(self, message: str) -> None:
        """
        无对局时用于展示提示信息（例如未 start 前的 who/login/register/seat 等）。
        """
        max_size = len(self.board_buttons)
        for y in range(max_size):
            for x in range(max_size):
                btn = self.board_buttons[y][x]
                try:
                    if self._default_btn_bg is not None:
                        btn.configure(text="", state=tk.DISABLED, bg=self._default_btn_bg)
                    else:
                        btn.configure(text="", state=tk.DISABLED)
                except Exception:
                    pass

        self.info_label.config(text=message or "")
        self.result_label.config(text="")
        self.turn_label.config(text="")
        if self.players_label is not None:
            self.players_label.config(text="Players: Black=Guest | White=Guest")

    def render_message_with_players(self, players: Dict, message: str) -> None:
        """
        无对局时展示信息，并同步更新玩家信息（用于 GUI 的 register/login/seat/who 等）。
        """
        self.render_message(message)
        if self.players_label is None:
            return
        black_entry = players.get(PlayerColor.BLACK.value) or {}
        white_entry = players.get(PlayerColor.WHITE.value) or {}
        self.players_label.config(
            text=f"Players: Black={_format_player(black_entry)} | White={_format_player(white_entry)}"
        )


def _format_player(entry: Dict) -> str:
    label = entry.get("label") or "Guest"
    kind = entry.get("kind")
    if kind == "ai":
        return str(label)
    wins = entry.get("wins")
    games = entry.get("games")
    if label != "Guest" and wins is not None and games is not None:
        return f"{label} ({wins}/{games})"
    return str(label)

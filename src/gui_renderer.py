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
    ) -> None:
        self.board_buttons = board_buttons
        self.info_label = info_label
        self.result_label = result_label
        self.turn_label = turn_label

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

        # 更新棋盘按钮：只在 0..size-1 范围内启用并显示棋子，其余禁用清空
        max_size = len(self.board_buttons)
        for y in range(max_size):
            for x in range(max_size):
                btn = self.board_buttons[y][x]
                if x < size and y < size:
                    cell = board[y][x]
                    if cell == PlayerColor.BLACK.value:
                        text = "●"
                    elif cell == PlayerColor.WHITE.value:
                        text = "○"
                    else:
                        text = "+"
                    btn.configure(text=text, state=tk.NORMAL)
                else:
                    btn.configure(text="", state=tk.DISABLED)

        # 信息提示
        self.info_label.config(text=message or "")

        # 结果与轮次
        if ended:
            if last_result:
                self.result_label.config(text=last_result_msg)
            else:
                self.result_label.config(text="Game ended")
            self.turn_label.config(text="")
        else:
            self.result_label.config(text="")
            if to_move:
                player = "Black" if to_move == PlayerColor.BLACK.value else "White"
                self.turn_label.config(text=f"{player} to move")
            else:
                self.turn_label.config(text="")


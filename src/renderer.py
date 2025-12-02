from typing import Dict, List, Optional

from src.core.player import PlayerColor


class CliRenderer:
    """
    文本渲染器：在控制台打印棋盘与消息。
    """

    def __init__(self, show_hint: bool = True):
        self.show_hint = show_hint

    def render(self, snapshot: Dict, message: Optional[str] = "") -> None:
        size = snapshot["size"]
        board: List[List[Optional[str]]] = snapshot["board"]
        to_move = snapshot.get("to_move")
        ended = snapshot.get("ended", False)
        last_result = snapshot.get("last_result")
        last_result_msg = snapshot.get("last_result_msg", "")

        # 列坐标
        header = "   " + " ".join([f"{i:2d}" for i in range(size)])
        print(header)
        for y in range(size):
            row_cells = []
            for x in range(size):
                cell = board[y][x]
                if cell == PlayerColor.BLACK.value:
                    row_cells.append("●")
                elif cell == PlayerColor.WHITE.value:
                    row_cells.append("○")
                else:
                    row_cells.append("+")
            print(f"{y:2d} " + " ".join(row_cells))

        if message:
            print(f"[info] {message}")
        if ended:
            if last_result:
                print(f"[result] {last_result_msg}")
            else:
                print("[result] Game ended")
        elif to_move:
            player = "Black" if to_move == PlayerColor.BLACK.value else "White"
            print(f"[turn] {player} to move")

        if self.show_hint:
            # 简要提示命令格式，save/load 提醒可指定名称
            print(
                "Commands: start go|gomoku [size] | play x y | pass (go only) | "
                "undo | resign | restart [size] | save name | load [name] | "
                "hint on/off | quit"
            )

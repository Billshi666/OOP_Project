import tkinter as tk
from tkinter import messagebox, simpledialog

from src.command_parser import Command
from src.controller import Controller
from src.gui_renderer import GuiRenderer


MAX_BOARD_SIZE = 19


class GuiApp:
    """
    简单的 Tkinter 界面，将鼠标点击和按钮操作映射为 Command，
    交给原有 Controller 处理，从而在不修改核心逻辑的前提下增加 GUI。
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Board Game Platform (Go / Gomoku) - GUI")

        # 左侧棋盘，右侧控制区，下方信息区
        self.board_frame = tk.Frame(self.root)
        self.controls_frame = tk.Frame(self.root)
        self.info_frame = tk.Frame(self.root)

        self.board_frame.grid(row=0, column=0, padx=10, pady=10)
        self.controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        self.info_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="we")

        # 棋盘按钮网格（最大 19x19，具体启用尺寸随游戏变化）
        self.board_buttons = self._create_board_buttons()
        # 初始全部禁用，等待 start
        self._enable_board(0)

        # 信息标签
        self.info_label = tk.Label(self.info_frame, text="", anchor="w")
        self.result_label = tk.Label(self.info_frame, text="", fg="blue", anchor="w")
        self.turn_label = tk.Label(self.info_frame, text="", fg="green", anchor="w")
        self.info_label.pack(fill="x")
        self.result_label.pack(fill="x")
        self.turn_label.pack(fill="x")

        # 控制区控件（游戏类型选择、尺寸输入、命令按钮）
        self._create_controls()

        # 使用 GUI 渲染器替换 CLI 渲染器，其余 Controller / Game 逻辑保持不变
        self.renderer = GuiRenderer(
            board_buttons=self.board_buttons,
            info_label=self.info_label,
            result_label=self.result_label,
            turn_label=self.turn_label,
        )
        self.controller = Controller(renderer=self.renderer)

    # --- UI 构建 ---

    def _create_board_buttons(self):
        buttons: list[list[tk.Button]] = []
        for y in range(MAX_BOARD_SIZE):
            row: list[tk.Button] = []
            for x in range(MAX_BOARD_SIZE):
                btn = tk.Button(
                    self.board_frame,
                    text="",
                    width=2,
                    height=1,
                    command=lambda xx=x, yy=y: self.on_cell_click(xx, yy),
                )
                btn.grid(row=y, column=x)
                row.append(btn)
            buttons.append(row)
        return buttons

    def _create_controls(self) -> None:
        # 游戏类型选择
        tk.Label(self.controls_frame, text="Game Type:").grid(row=0, column=0, sticky="w")
        self.game_type_var = tk.StringVar(value="go")
        tk.Radiobutton(
            self.controls_frame, text="Go", variable=self.game_type_var, value="go"
        ).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(
            self.controls_frame, text="Gomoku", variable=self.game_type_var, value="gomoku"
        ).grid(row=1, column=1, sticky="w")

        # 棋盘尺寸输入
        tk.Label(self.controls_frame, text="Board Size (8-19):").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(5, 0)
        )
        self.size_entry = tk.Entry(self.controls_frame, width=5)
        self.size_entry.insert(0, "19")
        self.size_entry.grid(row=3, column=0, sticky="w")

        # 控制按钮
        row = 4
        tk.Button(self.controls_frame, text="Start", command=self.on_start).grid(
            row=row, column=0, sticky="we", pady=2
        )
        tk.Button(self.controls_frame, text="Restart", command=self.on_restart).grid(
            row=row, column=1, sticky="we", pady=2
        )
        row += 1
        tk.Button(self.controls_frame, text="Undo", command=self.on_undo).grid(
            row=row, column=0, sticky="we", pady=2
        )
        tk.Button(self.controls_frame, text="Pass (Go)", command=self.on_pass).grid(
            row=row, column=1, sticky="we", pady=2
        )
        row += 1
        tk.Button(self.controls_frame, text="Resign", command=self.on_resign).grid(
            row=row, column=0, sticky="we", pady=2
        )
        row += 1
        tk.Button(self.controls_frame, text="Save", command=self.on_save).grid(
            row=row, column=0, sticky="we", pady=2
        )
        tk.Button(self.controls_frame, text="Load", command=self.on_load).grid(
            row=row, column=1, sticky="we", pady=2
        )

    # --- 事件处理 ---

    def _enable_board(self, size: int) -> None:
        """
        启用 0..size-1 范围内的按钮，其余禁用。
        """
        for y in range(MAX_BOARD_SIZE):
            for x in range(MAX_BOARD_SIZE):
                btn = self.board_buttons[y][x]
                if x < size and y < size:
                    btn.configure(state=tk.NORMAL)
                else:
                    btn.configure(state=tk.DISABLED, text="")

    def on_start(self) -> None:
        game_type = self.game_type_var.get()
        size_str = self.size_entry.get().strip()
        args = [game_type]
        if size_str:
            args.append(size_str)
        cmd = Command(name="start", args=args)
        self.controller.handle(cmd)
        # 根据实际棋盘大小启用对应按钮
        if self.controller.game:
            size = self.controller.game.board.size
            self._enable_board(size)

    def on_restart(self) -> None:
        # Restart 当前游戏类型，尺寸取输入框（若为空则沿用当前尺寸）
        if not self.controller.game:
            messagebox.showinfo("提示", "当前没有正在进行的对局")
            return
        size_str = self.size_entry.get().strip()
        args = []
        if size_str:
            args.append(size_str)
        cmd = Command(name="restart", args=args)
        self.controller.handle(cmd)
        # 更新棋盘启用区域
        if self.controller.game:
            size = self.controller.game.board.size
            self._enable_board(size)

    def on_cell_click(self, x: int, y: int) -> None:
        # 没有开始游戏时提示用户；避免调用原有控制器的 print 分支
        if not self.controller.game:
            messagebox.showinfo("提示", "请先开始游戏（Start）")
            return
        cmd = Command(name="play", args=[str(x), str(y)])
        self.controller.handle(cmd)

    def on_pass(self) -> None:
        # 仅 Go 有意义，但直接交给控制器，由规则决定是否允许
        if not self.controller.game:
            messagebox.showinfo("提示", "请先开始游戏")
            return
        cmd = Command(name="pass", args=[])
        self.controller.handle(cmd)

    def on_undo(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("提示", "当前没有正在进行的对局")
            return
        cmd = Command(name="undo", args=[])
        self.controller.handle(cmd)

    def on_resign(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("提示", "当前没有正在进行的对局")
            return
        cmd = Command(name="resign", args=[])
        self.controller.handle(cmd)

    def on_save(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("提示", "当前没有正在进行的对局")
            return
        name = simpledialog.askstring("保存对局", "请输入存档名称（如 game1）")
        if not name:
            return
        cmd = Command(name="save", args=[name.strip()])
        self.controller.handle(cmd)

    def on_load(self) -> None:
        # 允许用户选择名称，也允许留空加载上一局
        name = simpledialog.askstring("读取对局", "请输入存档名称（留空则读取上一局）")
        if name is None:
            return
        args = [name.strip()] if name.strip() else []
        cmd = Command(name="load", args=args)
        self.controller.handle(cmd)
        # 载入成功后，如果有 game 则启用对应尺寸
        if self.controller.game:
            size = self.controller.game.board.size
            self._enable_board(size)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
        app = GuiApp()
        app.run()


if __name__ == "__main__":
    main()

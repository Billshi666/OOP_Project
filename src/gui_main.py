import tkinter as tk
from tkinter import messagebox, simpledialog

from src.command_parser import Command
from src.controller import Controller
from src.core.player import PlayerColor
from src.gui_renderer import GuiRenderer


MAX_BOARD_SIZE = 19


class GuiApp:
    """
    简单的 Tkinter 界面，将鼠标点击和按钮操作映射为 Command，
    交给原有 Controller 处理，从而在不修改核心逻辑的前提下增加 GUI。
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Board Game Platform (Go / Gomoku / Othello) - GUI")

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
        self.info_label = tk.Label(self.info_frame, text="", anchor="w", justify="left", wraplength=820)
        self.result_label = tk.Label(self.info_frame, text="", fg="blue", anchor="w")
        self.turn_label = tk.Label(self.info_frame, text="", fg="green", anchor="w")
        self.players_label = tk.Label(self.info_frame, text="", anchor="w")
        self.info_label.pack(fill="x")
        self.result_label.pack(fill="x")
        self.turn_label.pack(fill="x")
        self.players_label.pack(fill="x")

        # 控制区控件（游戏类型选择、尺寸输入、命令按钮）
        self._create_controls()

        # 使用 GUI 渲染器替换 CLI 渲染器，其余 Controller / Game 逻辑保持不变
        self.renderer = GuiRenderer(
            board_buttons=self.board_buttons,
            info_label=self.info_label,
            result_label=self.result_label,
            turn_label=self.turn_label,
            players_label=self.players_label,
        )
        self.controller = Controller(renderer=self.renderer, password_prompt=self._prompt_password)
        self.renderer.render_message(
            "\n".join(
                [
                    "Welcome to Board Game Platform (GUI).",
                    "1) Choose a game type and board size, then click Start.",
                    "2) Seats: Human / AI1 / AI2 (AI is Othello-only).",
                    "3) Accounts: Register/Login per side; click Who to view players.",
                    "4) Save/Load/Replay use names stored in saves/ (e.g. game1).",
                    "Tip: in Othello, click Moves to highlight legal moves ('*').",
                ]
            )
        )
        self._sync_after_command()

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
            self.controls_frame,
            text="Go",
            variable=self.game_type_var,
            value="go",
            command=self._on_game_type_changed,
        ).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(
            self.controls_frame,
            text="Gomoku",
            variable=self.game_type_var,
            value="gomoku",
            command=self._on_game_type_changed,
        ).grid(row=1, column=1, sticky="w")
        tk.Radiobutton(
            self.controls_frame,
            text="Othello",
            variable=self.game_type_var,
            value="othello",
            command=self._on_game_type_changed,
        ).grid(row=1, column=2, sticky="w")

        # 棋盘尺寸输入
        self.size_label = tk.Label(self.controls_frame, text="Board Size:")
        self.size_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))
        self.size_entry = tk.Entry(self.controls_frame, width=5)
        self.size_entry.insert(0, "19")
        self.size_entry.grid(row=3, column=0, sticky="w")
        self._on_game_type_changed()

        # 控制按钮
        row = 4
        self.start_btn = tk.Button(self.controls_frame, text="Start", command=self.on_start)
        self.restart_btn = tk.Button(self.controls_frame, text="Restart", command=self.on_restart)
        self.start_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.restart_btn.grid(row=row, column=1, sticky="we", pady=2)
        row += 1
        self.undo_btn = tk.Button(self.controls_frame, text="Undo", command=self.on_undo)
        self.pass_btn = tk.Button(self.controls_frame, text="Pass (Go)", command=self.on_pass)
        self.undo_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.pass_btn.grid(row=row, column=1, sticky="we", pady=2)
        row += 1
        self.resign_btn = tk.Button(self.controls_frame, text="Resign", command=self.on_resign)
        self.moves_btn = tk.Button(self.controls_frame, text="Moves (Othello)", command=self.on_moves)
        self.resign_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.moves_btn.grid(row=row, column=1, sticky="we", pady=2)
        row += 1
        self.save_btn = tk.Button(self.controls_frame, text="Save", command=self.on_save)
        self.load_btn = tk.Button(self.controls_frame, text="Load", command=self.on_load)
        self.save_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.load_btn.grid(row=row, column=1, sticky="we", pady=2)
        row += 1
        self.replay_btn = tk.Button(self.controls_frame, text="Replay", command=self.on_replay)
        self.who_btn = tk.Button(self.controls_frame, text="Who", command=self.on_who)
        self.replay_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.who_btn.grid(row=row, column=1, sticky="we", pady=2)

        # Seat / Accounts
        row += 1
        tk.Label(self.controls_frame, text="Seats:").grid(row=row, column=0, sticky="w", pady=(8, 0))
        row += 1
        self.black_player_label = tk.Label(self.controls_frame, text="Black: Guest", anchor="w")
        self.white_player_label = tk.Label(self.controls_frame, text="White: Guest", anchor="w")
        self.black_player_label.grid(row=row, column=0, sticky="w")
        self.white_player_label.grid(row=row, column=1, sticky="w")
        row += 1
        self.black_seat_var = tk.StringVar(value="Human")
        self.white_seat_var = tk.StringVar(value="Human")
        self.black_seat_menu = tk.OptionMenu(
            self.controls_frame,
            self.black_seat_var,
            "Human",
            "AI1",
            "AI2",
            command=lambda _v: self.on_seat_change("black"),
        )
        self.white_seat_menu = tk.OptionMenu(
            self.controls_frame,
            self.white_seat_var,
            "Human",
            "AI1",
            "AI2",
            command=lambda _v: self.on_seat_change("white"),
        )
        self.black_seat_menu.grid(row=row, column=0, sticky="we", pady=2)
        self.white_seat_menu.grid(row=row, column=1, sticky="we", pady=2)

        row += 1
        self.black_register_btn = tk.Button(
            self.controls_frame, text="Register (Black)", command=lambda: self.on_register("black")
        )
        self.white_register_btn = tk.Button(
            self.controls_frame, text="Register (White)", command=lambda: self.on_register("white")
        )
        self.black_register_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.white_register_btn.grid(row=row, column=1, sticky="we", pady=2)

        row += 1
        self.black_login_btn = tk.Button(
            self.controls_frame, text="Login (Black)", command=lambda: self.on_login("black")
        )
        self.white_login_btn = tk.Button(
            self.controls_frame, text="Login (White)", command=lambda: self.on_login("white")
        )
        self.black_login_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.white_login_btn.grid(row=row, column=1, sticky="we", pady=2)

        row += 1
        self.black_logout_btn = tk.Button(
            self.controls_frame, text="Logout (Black)", command=lambda: self.on_logout("black")
        )
        self.white_logout_btn = tk.Button(
            self.controls_frame, text="Logout (White)", command=lambda: self.on_logout("white")
        )
        self.black_logout_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.white_logout_btn.grid(row=row, column=1, sticky="we", pady=2)

        # Replay navigation (enabled only in replay mode)
        row += 1
        tk.Label(self.controls_frame, text="Replay Controls:").grid(row=row, column=0, sticky="w", pady=(8, 0))
        row += 1
        self.prev_btn = tk.Button(self.controls_frame, text="Prev", command=self.on_prev)
        self.next_btn = tk.Button(self.controls_frame, text="Next", command=self.on_next)
        self.prev_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.next_btn.grid(row=row, column=1, sticky="we", pady=2)
        row += 1
        self.jump_btn = tk.Button(self.controls_frame, text="Jump", command=self.on_jump)
        self.exit_replay_btn = tk.Button(self.controls_frame, text="Exit Replay", command=self.on_exit_replay)
        self.jump_btn.grid(row=row, column=0, sticky="we", pady=2)
        self.exit_replay_btn.grid(row=row, column=1, sticky="we", pady=2)

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
        self._sync_after_command()

    def on_restart(self) -> None:
        # Restart 当前游戏类型，尺寸取输入框（若为空则沿用当前尺寸）
        if not self.controller.game:
            messagebox.showinfo("Info", "No game in progress.")
            return
        size_str = self.size_entry.get().strip()
        args = []
        if size_str:
            args.append(size_str)
        cmd = Command(name="restart", args=args)
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_cell_click(self, x: int, y: int) -> None:
        if self.controller.replay:
            return
        # 没有开始游戏时提示用户；避免调用原有控制器的 print 分支
        if not self.controller.game:
            messagebox.showinfo("Info", "Start a game first (click Start).")
            return
        cmd = Command(name="play", args=[str(x), str(y)])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_pass(self) -> None:
        # 仅 Go 有意义，但直接交给控制器，由规则决定是否允许
        if not self.controller.game:
            messagebox.showinfo("Info", "Start a game first.")
            return
        cmd = Command(name="pass", args=[])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_undo(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("Info", "No game in progress.")
            return
        cmd = Command(name="undo", args=[])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_resign(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("Info", "No game in progress.")
            return
        cmd = Command(name="resign", args=[])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_moves(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("Info", "Start a game first.")
            return
        cmd = Command(name="moves", args=[])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_save(self) -> None:
        if not self.controller.game:
            messagebox.showinfo("Info", "No game in progress.")
            return
        name = simpledialog.askstring("Save Game", "Enter save name (e.g. game1):")
        if not name:
            return
        cmd = Command(name="save", args=[name.strip()])
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_load(self) -> None:
        # 允许用户选择名称，也允许留空加载上一局
        name = simpledialog.askstring("Load Game", "Enter save name (leave empty to load last saved game):")
        if name is None:
            return
        args = [name.strip()] if name.strip() else []
        cmd = Command(name="load", args=args)
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_replay(self) -> None:
        name = simpledialog.askstring("Replay", "Enter save name (leave empty to replay last saved game):")
        if name is None:
            return
        args = [name.strip()] if name.strip() else []
        cmd = Command(name="replay", args=args)
        self.controller.handle(cmd)
        self._sync_after_command()

    def on_prev(self) -> None:
        self.controller.handle(Command(name="prev", args=[]))
        self._sync_after_command()

    def on_next(self) -> None:
        self.controller.handle(Command(name="next", args=[]))
        self._sync_after_command()

    def on_jump(self) -> None:
        val = simpledialog.askstring("Jump", "Jump to index (0-based):")
        if val is None:
            return
        val = val.strip()
        if not val:
            return
        self.controller.handle(Command(name="jump", args=[val]))
        self._sync_after_command()

    def on_exit_replay(self) -> None:
        self.controller.handle(Command(name="exit", args=[]))
        self._sync_after_command()

    def on_who(self) -> None:
        self.controller.handle(Command(name="who", args=[]))
        self._sync_after_command()

    def on_seat_change(self, side: str) -> None:
        value = self.black_seat_var.get() if side == "black" else self.white_seat_var.get()
        kind = value.lower()
        cmd_kind = "human" if kind == "human" else kind
        self.controller.handle(Command(name="seat", args=[side, cmd_kind]))
        self._sync_after_command()

    def on_register(self, side: str) -> None:
        username = simpledialog.askstring("Register", f"Username for {side}:")
        if not username:
            return
        self.controller.handle(Command(name="register", args=[side, username.strip()]))
        self._sync_after_command()

    def on_login(self, side: str) -> None:
        username = simpledialog.askstring("Login", f"Username for {side}:")
        if not username:
            return
        self.controller.handle(Command(name="login", args=[side, username.strip()]))
        self._sync_after_command()

    def on_logout(self, side: str) -> None:
        self.controller.handle(Command(name="logout", args=[side]))
        self._sync_after_command()

    def _prompt_password(self, prompt: str):
        return simpledialog.askstring("Password", prompt, show="*", parent=self.root)

    def _on_game_type_changed(self, *, adjust_size: bool = True) -> None:
        gt = self.game_type_var.get()
        if gt == "go":
            self.size_label.config(text="Board Size (Go: 8-19, default 19):")
            if adjust_size:
                self._set_size_if_empty_or_default(["15", "8"], "19")
        elif gt == "gomoku":
            self.size_label.config(text="Board Size (Gomoku: 8-19, default 15):")
            if adjust_size:
                self._set_size_if_empty_or_default(["19", "8"], "15")
        else:
            self.size_label.config(text="Board Size (Othello: even 8-18, default 8):")
            if adjust_size:
                self._set_size_if_empty_or_default(["19", "15"], "8")

    def _set_size_if_empty_or_default(self, defaults: list[str], new_default: str) -> None:
        cur = self.size_entry.get().strip()
        if not cur or cur in defaults:
            self.size_entry.delete(0, tk.END)
            self.size_entry.insert(0, new_default)

    def _sync_after_command(self) -> None:
        # 同步 board 可用区域与控件状态
        if self.controller.game and not self.controller.replay:
            self._enable_board(self.controller.game.board.size)
            # 同步选择项（例如 load 载入不同游戏类型）
            self.game_type_var.set(self.controller.game.name)
            self.size_entry.delete(0, tk.END)
            self.size_entry.insert(0, str(self.controller.game.board.size))
            self._on_game_type_changed(adjust_size=False)
        self._set_replay_mode(bool(self.controller.replay))
        self._sync_seat_and_account_controls()

    def _set_replay_mode(self, enabled: bool) -> None:
        # Replay mode 下禁用对局操作，只保留回放导航
        normal_state = tk.DISABLED if enabled else tk.NORMAL
        replay_state = tk.NORMAL if enabled else tk.DISABLED

        for widget in [
            self.start_btn,
            self.restart_btn,
            self.undo_btn,
            self.pass_btn,
            self.resign_btn,
            self.moves_btn,
            self.save_btn,
            self.load_btn,
            self.replay_btn,
            self.who_btn,
            self.black_seat_menu,
            self.white_seat_menu,
            self.black_register_btn,
            self.white_register_btn,
            self.black_login_btn,
            self.white_login_btn,
            self.black_logout_btn,
            self.white_logout_btn,
        ]:
            widget.configure(state=normal_state)

        for widget in [self.prev_btn, self.next_btn, self.jump_btn, self.exit_replay_btn]:
            widget.configure(state=replay_state)

        if enabled:
            # keep current replay board visible, but disable clicks
            for row in self.board_buttons:
                for btn in row:
                    btn.configure(state=tk.DISABLED)
        else:
            if self.controller.game:
                self._enable_board(self.controller.game.board.size)
            else:
                self._enable_board(0)

    def _sync_seat_and_account_controls(self) -> None:
        # Seat 下拉框显示与登录按钮可用性
        def to_label(seat) -> str:
            if seat.kind == "ai":
                return f"AI{seat.ai_level or 1}"
            return "Human"

        def player_display(color: PlayerColor) -> str:
            seat = self.controller.seats[color]
            if seat.kind == "ai":
                return f"AI{seat.ai_level or 1}"
            if seat.username:
                try:
                    stats = self.controller.accounts.get_stats(seat.username)
                    return f"{seat.username} ({stats.wins}/{stats.games})"
                except Exception:
                    return seat.username
            return "Guest"

        b = self.controller.seats[PlayerColor.BLACK]
        w = self.controller.seats[PlayerColor.WHITE]

        self.black_seat_var.set(to_label(b))
        self.white_seat_var.set(to_label(w))
        self.black_player_label.config(text=f"Black: {player_display(PlayerColor.BLACK)}")
        self.white_player_label.config(text=f"White: {player_display(PlayerColor.WHITE)}")

        # Accounts 按钮：AI 时禁用
        black_accounts_state = tk.NORMAL if b.kind == "human" and not self.controller.replay else tk.DISABLED
        white_accounts_state = tk.NORMAL if w.kind == "human" and not self.controller.replay else tk.DISABLED
        for widget in [self.black_register_btn, self.black_login_btn, self.black_logout_btn]:
            widget.configure(state=black_accounts_state)
        for widget in [self.white_register_btn, self.white_login_btn, self.white_logout_btn]:
            widget.configure(state=white_accounts_state)

        # Pass/Moves 仅对特定游戏启用
        if self.controller.game and not self.controller.replay:
            self.pass_btn.configure(state=tk.NORMAL if self.controller.game.name == "go" else tk.DISABLED)
            self.moves_btn.configure(state=tk.NORMAL if self.controller.game.name == "othello" else tk.DISABLED)
        else:
            self.pass_btn.configure(state=tk.DISABLED)
            self.moves_btn.configure(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = GuiApp()
    app.run()


if __name__ == "__main__":
    main()

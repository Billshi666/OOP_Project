import os
import random
from datetime import datetime, timezone
from getpass import getpass
from typing import Callable, Optional
from src.accounts import AccountManager
from src.command_parser import Command
from src.ai_othello import choose_othello_move
from src.core.move import Move
from src.core.player import PlayerColor
from src.game.factory import GameFactory
from src.game.base_game import Game
from src.game.go_game import GoGame
from src.game.gomoku_game import GomokuGame
from src.game.othello_game import OthelloGame
from src.renderer import CliRenderer
from src.replay import ReplaySession
from src.seat import Seat
from src.serializer import JsonSerializer


class Controller:
    """
    协调命令解析、游戏逻辑与渲染。
    """

    def __init__(
        self,
        renderer: Optional[CliRenderer] = None,
        password_prompt: Optional[Callable[[str], Optional[str]]] = None,
    ):
        self.renderer = renderer or CliRenderer()
        self.game: Optional[Game] = None
        self.replay: Optional[ReplaySession] = None
        # 记录最近一次成功存档的完整路径，便于默认恢复上一局
        self.last_save_path: Optional[str] = None
        # 对弈双方配置：默认都是人类游客
        self.seats = {
            PlayerColor.BLACK: Seat(kind="human"),
            PlayerColor.WHITE: Seat(kind="human"),
        }
        self._rng = random.Random()
        self.accounts = AccountManager()
        self._last_ended_state: bool = False
        self._applied_account_deltas: list[tuple[str, int, int]] = []
        self._password_prompt = password_prompt or self._cli_password_prompt

    def handle(self, cmd: Command) -> bool:
        """
        处理命令。返回 False 表示退出循环。
        """
        name = cmd.name
        args = cmd.args

        if self.replay:
            return self._handle_replay_mode(cmd)

        if name == "quit" or name == "exit":
            print("Bye.")
            return False

        if name == "help":
            self._print_help(args)
            return True

        if name == "hint" and args:
            self.renderer.show_hint = args[0].lower() == "on"
            self._render("Hint " + ("on" if self.renderer.show_hint else "off"))
            return True

        if name == "seat":
            self._handle_seat(args)
            self._auto_advance()
            return True

        if name == "register":
            self._handle_register(args)
            return True

        if name == "login":
            self._handle_login(args)
            return True

        if name == "logout":
            self._handle_logout(args)
            return True

        if name == "who":
            self._render(self._who_message())
            return True

        if name == "replay":
            self._handle_replay(args)
            return True

        if name == "start":
            self._handle_start(args)
            self._auto_advance()
            return True

        if name == "restart":
            self._handle_restart(args)
            self._auto_advance()
            return True

        if name == "load":
            # 不带参数时，尝试恢复上一局
            if not args:
                if self.last_save_path:
                    self._handle_load(self.last_save_path)
                else:
                    self._render("Usage: load name_or_path  (or omit name after a save to load last game)")
                self._auto_advance()
                return True
            self._handle_load(self._resolve_path(args[0], for_save=False))
            self._auto_advance()
            return True

        # 以下命令需要已有游戏
        if not self.game:
            print("Start a game first: start go|gomoku|othello [size]")
            print("Tip: type 'help' for examples (e.g. start othello 8)")
            return True

        if name == "moves":
            self._handle_moves()
            return True

        if name == "play" and len(args) == 2:
            if self._is_ai_turn():
                side = "black" if self.game.to_move == PlayerColor.BLACK else "white"
                self._render(
                    "\n".join(
                        [
                            "It's AI's turn. AI moves automatically.",
                            f"To take over: seat {side} human",
                        ]
                    )
                )
                self._auto_advance()
                return True
            try:
                x, y = int(args[0]), int(args[1])
            except ValueError:
                self._render("Invalid coordinates. Usage: play x y")
                return True
            move = Move(x=x, y=y, color=self.game.to_move, is_pass=False)
            result = self.game.play_move(move)
            self._render(self._decorate_result_message(result.message))
            self._after_state_change()
            self._auto_advance()
            return True

        if name == "pass":
            if self._is_ai_turn():
                side = "black" if self.game.to_move == PlayerColor.BLACK else "white"
                self._render(
                    "\n".join(
                        [
                            "It's AI's turn. AI moves automatically.",
                            f"To take over: seat {side} human",
                        ]
                    )
                )
                self._auto_advance()
                return True
            result = self.game.pass_move()
            self._render(self._decorate_result_message(result.message))
            self._after_state_change()
            self._auto_advance()
            return True

        if name == "undo":
            result = self.game.undo()
            self._render(self._decorate_result_message(result.message))
            self._after_state_change()
            self._auto_advance()
            return True

        if name == "resign":
            result = self.game.resign()
            self._render(result.message)
            self._after_state_change()
            return True

        if name == "save" and args:
            try:
                raw_name = args[0]
                path = self._resolve_path(raw_name, for_save=True)
                self.game.save(path, meta=self._build_save_meta())
                self.last_save_path = path
                self._associate_recording_with_accounts(path)
                self._render(
                    "\n".join(
                        [
                            f"Saved to {path}  (use 'load {raw_name}' or 'load' to restore)",
                            f"Tip: replay {raw_name}",
                        ]
                    )
                )
            except Exception as e:
                self._render(f"Save failed: {e}")
            return True

        if name == "save" and not args:
            # 提示使用方式与命名建议
            self._render("Usage: save name  (stored as saves/name.json)")
            return True

        self._render("Unknown or malformed command. Type 'help' to see examples.")
        return True

    # 内部帮助
    def _print_help(self, args: list[str]) -> None:
        topic = args[0].lower() if args else "general"

        if topic in ("accounts", "account", "login", "register", "logout"):
            print(
                "\n".join(
                    [
                        "Help - Accounts (all games)",
                        "",
                        "Commands:",
                        "  register black|white <username>   # prompts for password (not echoed)",
                        "  login black|white <username>      # prompts for password (not echoed)",
                        "  logout black|white",
                        "  who                               # show Guest / username (wins/games) / AI",
                        "",
                        "Notes:",
                        "  - Stats are updated when a game ends (wins/games; draw counts as a game).",
                        "  - Account data is saved locally in saves/accounts.json.",
                        "  - Save files are associated with logged-in users when you run 'save'.",
                    ]
                )
            )
            return

        if topic in ("ai", "bot"):
            print(
                "\n".join(
                    [
                        "Help - AI (Othello only)",
                        "",
                        "Enable AI:",
                        "  seat black|white ai1",
                        "  seat black|white ai2",
                        "  seat black|white human   # take over from AI",
                        "",
                        "Behavior:",
                        "  - AI moves automatically on its turns (supports Human-AI and AI-AI).",
                        "  - ai1: random legal move",
                        "  - ai2: simple heuristic (usually beats ai1)",
                        "",
                        "Tips:",
                        "  - Use 'moves' to see legal moves as '*' on the board.",
                    ]
                )
            )
            return

        if topic in ("replay", "recording", "playback"):
            print(
                "\n".join(
                    [
                        "Help - Replay",
                        "",
                        "Enter replay mode:",
                        "  replay name          # loads saves/name.json",
                        "  replay               # replays the last saved game (after 'save')",
                        "",
                        "Replay mode commands:",
                        "  next | prev | jump n | exit | quit",
                        "",
                        "Notes:",
                        "  - The info line shows the move coordinate and extra info (flips/captures) when available.",
                    ]
                )
            )
            return

        if topic in ("othello", "reversi"):
            print(
                "\n".join(
                    [
                        "Help - Othello (Reversi)",
                        "",
                        "Start:",
                        "  start othello [size]   # even size 8-18, default 8",
                        "",
                        "Rules (summary):",
                        "  - You must place on an empty cell that flips at least one opponent disc.",
                        "  - If you have no legal move, the game forces a pass automatically.",
                        "  - Game ends when board is full or both players have no legal moves.",
                        "",
                        "Useful commands:",
                        "  moves                  # shows legal moves as '*' on the board",
                        "  seat black|white ai1|ai2|human",
                    ]
                )
            )
            return

        print(
            "\n".join(
                [
                    "Board Game Platform - Help",
                    "",
                    "Quickstart (Othello + AI):",
                    "  start othello 8",
                    "  moves",
                    "  seat white ai1",
                    "  play 2 3",
                    "  save game1",
                    "  replay game1",
                    "",
                    "Start:",
                    "  start go [size]            # size 8-19, default 19",
                    "  start gomoku [size]        # size 8-19, default 15",
                    "  start othello [size]       # even size 8-18, default 8",
                    "",
                    "Play:",
                    "  play x y | undo | resign | restart [size]",
                    "  pass                       # go only (othello uses forced pass)",
                    "",
                    "Accounts (all games):",
                    "  register/login/logout black|white <username>   # password is not echoed",
                    "  who",
                    "",
                    "AI (Othello only):",
                    "  seat black|white human|ai1|ai2",
                    "",
                    "Replay:",
                    "  save name | load [name] | replay [name]",
                    "  (replay mode) next | prev | jump n | exit",
                    "",
                    "More help topics:",
                    "  help accounts | help ai | help othello | help replay",
                    "",
                    "Misc:",
                    "  hint on/off | quit",
                ]
            )
        )

    def _handle_seat(self, args):
        if len(args) != 2:
            self._render("Usage: seat black|white human|ai1|ai2")
            return
        side_raw, kind_raw = args[0].lower(), args[1].lower()
        color = self._parse_side(side_raw)
        if color is None:
            self._render("Seat failed: side must be black or white")
            return
        side = "black" if color == PlayerColor.BLACK else "white"

        if kind_raw == "human":
            current = self.seats[color]
            self.seats[color] = Seat(kind="human", username=current.username)
            lines = [f"{color.name} set to human"]
            if self.game and self.game.name == "othello":
                lines.append("Tip: enable AI: seat black|white ai1|ai2")
            self._render("\n".join(lines))
            return
        if kind_raw in ("ai1", "ai2"):
            level = 1 if kind_raw == "ai1" else 2
            self.seats[color] = Seat(kind="ai", ai_level=level, username=None)
            lines = [f"{color.name} set to AI{level}"]
            if not self.game:
                lines.append("Tip: start othello 8 to play with AI (AI is Othello-only)")
            elif self.game.name != "othello":
                lines.append("Note: AI is only supported in Othello (start othello 8)")
            else:
                lines.append("AI will move automatically on its turns.")
                lines.append(f"To take over: seat {side} human")
                lines.append("Tip: use 'moves' to see legal moves as '*'")
            self._render("\n".join(lines))
            return

        self._render("Seat failed: kind must be human|ai1|ai2")

    def _decorate_result_message(self, message: str) -> str:
        """
        给部分结果消息补充更明确的引导（仅输出层逻辑，不影响规则判定）。
        """
        if not self.game:
            return message

        if self.game.name == "othello":
            if message.startswith("Illegal move in Othello"):
                return "\n".join([message, "Tip: use 'moves' to show legal moves ('*' on the board)"])
            if message.startswith("Pass not allowed"):
                return "\n".join(
                    [
                        message,
                        "Tip: Othello uses forced pass automatically; play a legal move (try 'moves')",
                    ]
                )
            if message == "Forced pass (no legal moves)":
                return "\n".join([message, "Tip: this happens automatically when you have no legal moves"])

        if self.game.name == "gomoku" and message == "Pass not allowed in Gomoku":
            return "\n".join([message, "Tip: Gomoku does not support 'pass'"])

        return message

    def _handle_register(self, args) -> None:
        if len(args) != 2:
            self._render("Usage: register black|white <username>")
            return
        color = self._parse_side(args[0].lower())
        if color is None:
            self._render("Register failed: side must be black or white")
            return
        username = args[1]
        pwd1 = self._password_prompt("Password: ")
        if pwd1 is None:
            self._render("Register cancelled")
            return
        pwd2 = self._password_prompt("Confirm: ")
        if pwd2 is None:
            self._render("Register cancelled")
            return
        if pwd1 != pwd2:
            self._render("Register failed: passwords do not match")
            return
        try:
            self.accounts.register(username, pwd1)
            self.seats[color] = Seat(kind="human", username=username)
            self._render(
                "\n".join(
                    [
                        f"{color.name} registered and logged in as {username}",
                        "Tip: who",
                    ]
                )
            )
        except Exception as e:
            self._render(f"Register failed: {e}")

    def _handle_login(self, args) -> None:
        if len(args) != 2:
            self._render("Usage: login black|white <username>")
            return
        color = self._parse_side(args[0].lower())
        if color is None:
            self._render("Login failed: side must be black or white")
            return
        username = args[1]
        pwd = self._password_prompt("Password: ")
        if pwd is None:
            self._render("Login cancelled")
            return
        ok = self.accounts.authenticate(username, pwd)
        if not ok:
            self._render("Login failed: invalid username or password")
            return
        self.seats[color] = Seat(kind="human", username=username)
        self._render("\n".join([f"{color.name} logged in as {username}", "Tip: who"]))

    def _handle_logout(self, args) -> None:
        if len(args) != 1:
            self._render("Usage: logout black|white")
            return
        color = self._parse_side(args[0].lower())
        if color is None:
            self._render("Logout failed: side must be black or white")
            return
        current = self.seats[color]
        if current.kind != "human" or not current.username:
            self._render(f"{color.name} is already Guest")
            return
        self.seats[color] = Seat(kind="human", username=None)
        self._render("\n".join([f"{color.name} logged out", "Tip: who"]))

    def _cli_password_prompt(self, prompt: str) -> Optional[str]:
        """
        CLI 默认密码输入（不回显）。返回 None 表示用户取消/中断。
        """
        try:
            return getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            return None

    def _handle_start(self, args):
        if not args:
            self._render("Usage: start go|gomoku|othello [size]")
            return
        game_type = args[0]
        size = None
        if len(args) >= 2:
            try:
                size = int(args[1])
            except ValueError:
                self._render("Invalid size")
                return
        try:
            self.game = GameFactory.create(game_type, size)
            # 本阶段 AI 仅支持 Othello，启动其他游戏时自动重置 AI seat，避免用户卡死在“AI 回合”
            if self.game.name != "othello":
                changed = False
                for color in (PlayerColor.BLACK, PlayerColor.WHITE):
                    if self.seats[color].kind == "ai":
                        self.seats[color] = Seat(kind="human")
                        changed = True
                suffix = " (AI seats reset to human)" if changed else ""
            else:
                suffix = ""
            lines = [f"Started {game_type} size {self.game.board.size}{suffix}"]
            if self.game.name == "othello":
                lines.append("Tip: moves  # shows legal moves as '*'")
                lines.append("Tip: seat white ai1  # enable AI (Othello only)")
                lines.append("Tip: forced pass is automatic when you have no legal moves")
            else:
                lines.append("Tip: accounts work in all games: register/login ... | who")
            lines.append("Tip: save name  (then)  replay [name]")
            self._render("\n".join(lines))
            self._reset_end_tracking()
        except Exception as e:
            self._render(f"Start failed: {e}")

    def _handle_restart(self, args):
        if not self.game:
            self._render("No game to restart")
            return
        size = self.game.board.size
        if args:
            try:
                size = int(args[0])
            except ValueError:
                self._render("Invalid size")
                return
        # 重启直接用 start 重新创建游戏实例，保持流程一致
        self._handle_start([self.game.name, str(size)])

    def _handle_load(self, path: str):
        try:
            data = JsonSerializer().load(path)
        except Exception as e:
            self._render(f"Load failed: {e}")
            return
        game_type = data.get("game", "go")
        try:
            if game_type == "go":
                game = GoGame()
            elif game_type == "gomoku":
                game = GomokuGame()
            elif game_type == "othello":
                game = OthelloGame()
            else:
                raise ValueError("Unknown game type in save file")
            game._load_snapshot(data)  # 使用已有快照恢复
            self.game = game
            self.last_save_path = path
            if self.game.name != "othello":
                changed = False
                for color in (PlayerColor.BLACK, PlayerColor.WHITE):
                    if self.seats[color].kind == "ai":
                        self.seats[color] = Seat(kind="human")
                        changed = True
                suffix = " (AI seats reset to human)" if changed else ""
            else:
                suffix = ""
            self._render(f"Loaded {game_type} from {path}{suffix}")
            self._reset_end_tracking()
        except Exception as e:
            self._render(f"Load failed: {e}")

    def _render(self, message: str):
        if self.game:
            snapshot = self.game.get_snapshot()
            snapshot["players"] = self._players_snapshot()
            self.renderer.render(snapshot, message)
        else:
            # 无游戏时：CLI 直接打印；GUI 通过 renderer.render_message 展示
            if hasattr(self.renderer, "render_message_with_players"):
                try:
                    players = self._players_snapshot()
                    self.renderer.render_message_with_players(players, message)  # type: ignore[attr-defined]
                    return
                except Exception:
                    pass
            if hasattr(self.renderer, "render_message"):
                try:
                    self.renderer.render_message(message)  # type: ignore[attr-defined]
                    return
                except Exception:
                    pass
            if message:
                print(message)

    def _handle_moves(self) -> None:
        # 仅 Othello 支持“合法落子点”提示
        if not self.game or self.game.name != "othello":
            self._render("Legal moves visualization is only available in Othello")
            return
        engine = self.game.rule_engine
        if not hasattr(engine, "legal_moves"):
            self._render("Legal moves not available")
            return
        legal = engine.legal_moves(self.game.board, self.game.to_move)  # type: ignore[attr-defined]
        snapshot = self.game.get_snapshot()
        snapshot["players"] = self._players_snapshot()
        snapshot["legal_moves"] = legal
        snapshot["show_legal_moves"] = True
        self.renderer.render(
            snapshot,
            "\n".join(
                [
                    f"Legal moves for {self.game.to_move.name}: {len(legal)}",
                    "Tip: play x y on a '*' cell",
                ]
            ),
        )

    def _handle_replay(self, args) -> None:
        if args:
            path = self._resolve_path(args[0], for_save=False)
        else:
            if not self.last_save_path:
                self._render("Usage: replay name  (or replay after a save to replay last game)")
                return
            path = self.last_save_path
        try:
            data = JsonSerializer().load(path)
        except Exception as e:
            self._render(f"Replay failed: {e}")
            return
        session = ReplaySession(data)
        if not session.timeline:
            self._render("Replay failed: empty save")
            return
        self.replay = session
        self._render_replay()

    def _handle_replay_mode(self, cmd: Command) -> bool:
        name = cmd.name
        args = cmd.args
        if name == "quit":
            print("Bye.")
            return False
        if name == "exit":
            self.replay = None
            # 退出回放后，回到当前对局（若存在）或仅提示
            self._render("Exited replay mode")
            return True
        if name == "help":
            print("Replay mode: next | prev | jump n | exit | quit")
            return True
        if name == "hint" and args:
            self.renderer.show_hint = args[0].lower() == "on"
            self._render_replay()
            return True
        if name == "next":
            self.replay.next()  # type: ignore[union-attr]
            self._render_replay()
            return True
        if name == "prev":
            self.replay.prev()  # type: ignore[union-attr]
            self._render_replay()
            return True
        if name == "jump" and args:
            try:
                idx = int(args[0])
            except ValueError:
                self._render_replay(message_override="Invalid index")
                return True
            self.replay.jump(idx)  # type: ignore[union-attr]
            self._render_replay()
            return True
        self._render_replay(message_override="Replay mode: next | prev | jump n | exit | quit")
        return True

    def _render_replay(self, message_override: Optional[str] = None) -> None:
        if not self.replay:
            return
        snapshot = self.replay.current_snapshot()
        message = message_override if message_override is not None else self.replay.current_message()
        self.renderer.render(snapshot, message)

    def _auto_advance(self) -> None:
        """
        自动推进对局：
        - Othello：若当前方无合法落子，自动 forced pass；
        - 若当前方为 AI，自动落子，支持 Human-AI 与 AI-AI。
        """
        if not self.game or self.game.ended:
            return

        while self.game and not self.game.ended:
            # 1) Othello forced pass（人类与 AI 都一样处理）
            if self.game.name == "othello":
                engine = self.game.rule_engine
                if hasattr(engine, "legal_moves"):
                    legal = engine.legal_moves(self.game.board, self.game.to_move)  # type: ignore[attr-defined]
                    if not legal:
                        result = self.game.pass_move()
                        self._render(result.message)
                        self._after_state_change()
                        continue

            # 2) AI 自动走子
            if not self._is_ai_turn():
                break
            seat = self.seats[self.game.to_move]
            if self.game.name != "othello":
                self._render("AI is only supported in Othello for this stage")
                break
            engine = self.game.rule_engine
            if not hasattr(engine, "legal_moves"):
                break

            level = seat.ai_level or 1
            move = choose_othello_move(level, self.game.board, self.game.to_move, engine, rng=self._rng)  # type: ignore[arg-type]
            result = self.game.play_move(move)
            self._render(result.message)
            self._after_state_change()

    def _is_ai_turn(self) -> bool:
        if not self.game:
            return False
        if self.game.name != "othello":
            return False
        seat = self.seats.get(self.game.to_move)
        return bool(seat and seat.kind == "ai")

    def _players_snapshot(self) -> dict:
        """
        构造用于渲染显示的玩家信息（用户名/游客/AI）。
        """
        return {
            PlayerColor.BLACK.value: self._player_entry(PlayerColor.BLACK),
            PlayerColor.WHITE.value: self._player_entry(PlayerColor.WHITE),
        }

    def _parse_side(self, raw: str) -> Optional[PlayerColor]:
        if raw in ("black", "b"):
            return PlayerColor.BLACK
        if raw in ("white", "w"):
            return PlayerColor.WHITE
        return None

    def _player_entry(self, color: PlayerColor) -> dict:
        seat = self.seats[color]
        entry = {"label": seat.display_name(), "kind": seat.kind}
        if seat.kind == "human" and seat.username:
            try:
                stats = self.accounts.get_stats(seat.username)
                entry["games"] = stats.games
                entry["wins"] = stats.wins
            except Exception:
                entry["games"] = 0
                entry["wins"] = 0
        return entry

    def _who_message(self) -> str:
        b = self._player_entry(PlayerColor.BLACK)
        w = self._player_entry(PlayerColor.WHITE)
        return f"Black={self._format_player(b)} | White={self._format_player(w)}"

    def _format_player(self, entry: dict) -> str:
        label = entry.get("label", "Guest")
        if entry.get("kind") == "ai":
            return label
        if "games" in entry and "wins" in entry and label != "Guest":
            return f"{label} ({entry['wins']}/{entry['games']})"
        return label

    def _reset_end_tracking(self) -> None:
        if not self.game:
            self._last_ended_state = False
            self._applied_account_deltas = []
            return
        self._last_ended_state = bool(self.game.ended)
        self._applied_account_deltas = []

    def _after_state_change(self) -> None:
        if not self.game:
            return
        ended = bool(self.game.ended)
        if not self._last_ended_state and ended:
            self._apply_accounts_for_game_end()
        elif self._last_ended_state and not ended:
            self._rollback_accounts_for_undo()
        self._last_ended_state = ended

    def _apply_accounts_for_game_end(self) -> None:
        if not self.game or not self.game.last_result:
            return
        winner = self.game.last_result.winner
        deltas: list[tuple[str, int, int]] = []
        for color in (PlayerColor.BLACK, PlayerColor.WHITE):
            seat = self.seats[color]
            if seat.kind != "human" or not seat.username:
                continue
            won = winner == color if winner is not None else False
            try:
                games_inc, wins_inc = self.accounts.apply_game_result(seat.username, won=won)
                deltas.append((seat.username, games_inc, wins_inc))
            except Exception:
                continue
        self._applied_account_deltas = deltas

    def _rollback_accounts_for_undo(self) -> None:
        for username, games_inc, wins_inc in self._applied_account_deltas:
            try:
                self.accounts.rollback_game_result(username, games_inc, wins_inc)
            except Exception:
                continue
        self._applied_account_deltas = []

    def _associate_recording_with_accounts(self, path: str) -> None:
        for color in (PlayerColor.BLACK, PlayerColor.WHITE):
            seat = self.seats[color]
            if seat.kind == "human" and seat.username:
                try:
                    self.accounts.add_recording(seat.username, path)
                except Exception:
                    continue

    def _build_save_meta(self) -> dict:
        return {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "players": self._players_snapshot(),
        }

    def _resolve_path(self, name: str, for_save: bool) -> str:
        """
        统一处理存档路径：
        - 若 name 不包含路径分隔符，则存入 saves/ 目录，并自动补全 .json 后缀；
        - 否则视为用户指定完整路径；
        - for_save=True 时确保目标目录存在。
        """
        path = name
        if "/" not in name and "\\" not in name:
            base = name
            if not base.endswith(".json"):
                base += ".json"
            path = os.path.join("saves", base)
        if for_save:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

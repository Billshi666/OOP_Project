import os
from typing import Optional
from src.command_parser import Command
from src.core.move import Move
from src.core.player import PlayerColor
from src.game.factory import GameFactory
from src.game.base_game import Game
from src.game.go_game import GoGame
from src.game.gomoku_game import GomokuGame
from src.renderer import CliRenderer
from src.serializer import JsonSerializer


class Controller:
    """
    协调命令解析、游戏逻辑与渲染。
    """

    def __init__(self, renderer: Optional[CliRenderer] = None):
        self.renderer = renderer or CliRenderer()
        self.game: Optional[Game] = None
        # 记录最近一次成功存档的完整路径，便于默认恢复上一局
        self.last_save_path: Optional[str] = None

    def handle(self, cmd: Command) -> bool:
        """
        处理命令。返回 False 表示退出循环。
        """
        name = cmd.name
        args = cmd.args

        if name == "quit" or name == "exit":
            print("Bye.")
            return False

        if name == "hint" and args:
            self.renderer.show_hint = args[0].lower() == "on"
            self._render("Hint " + ("on" if self.renderer.show_hint else "off"))
            return True

        if name == "start":
            self._handle_start(args)
            return True

        if name == "restart":
            self._handle_restart(args)
            return True

        if name == "load":
            # 不带参数时，尝试恢复上一局
            if not args:
                if self.last_save_path:
                    self._handle_load(self.last_save_path)
                else:
                    self._render("Usage: load name_or_path  (or omit name after a save to load last game)")
                return True
            self._handle_load(self._resolve_path(args[0], for_save=False))
            return True

        # 以下命令需要已有游戏
        if not self.game:
            print("Start a game first: start go|gomoku [size]")
            return True

        if name == "play" and len(args) == 2:
            try:
                x, y = int(args[0]), int(args[1])
            except ValueError:
                self._render("Invalid coordinates")
                return True
            move = Move(x=x, y=y, color=self.game.to_move, is_pass=False)
            result = self.game.play_move(move)
            self._render(result.message)
            return True

        if name == "pass":
            result = self.game.pass_move()
            self._render(result.message)
            return True

        if name == "undo":
            result = self.game.undo()
            self._render(result.message)
            return True

        if name == "resign":
            result = self.game.resign()
            self._render(result.message)
            return True

        if name == "save" and args:
            try:
                raw_name = args[0]
                path = self._resolve_path(raw_name, for_save=True)
                self.game.save(path)
                self.last_save_path = path
                self._render(f"Saved to {path}  (use 'load {raw_name}' or 'load' to restore)")
            except Exception as e:
                self._render(f"Save failed: {e}")
            return True

        if name == "save" and not args:
            # 提示使用方式与命名建议
            self._render("Usage: save name  (stored as saves/name.json)")
            return True

        self._render("Unknown or malformed command")
        return True

    # 内部帮助
    def _handle_start(self, args):
        if not args:
            self._render("Usage: start go|gomoku [size]")
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
            self._render(f"Started {game_type} size {self.game.board.size}")
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
            else:
                game = GomokuGame()
            game._load_snapshot(data)  # 使用已有快照恢复
            self.game = game
            self.last_save_path = path
            self._render(f"Loaded {game_type} from {path}")
        except Exception as e:
            self._render(f"Load failed: {e}")

    def _render(self, message: str):
        if self.game:
            self.renderer.render(self.game.get_snapshot(), message)
        else:
            # 无游戏时只打印消息
            if message:
                print(message)

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

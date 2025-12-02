from typing import Optional

from src.game.base_game import Game, GameConfig
from src.game.go_game import GoGame
from src.game.gomoku_game import GomokuGame


class GameFactory:
    """
    抽象工厂：根据类型创建具体游戏实例。
    """

    @staticmethod
    def create(game_type: str, size: Optional[int] = None) -> Game:
        game_type = game_type.lower()
        if game_type == "go":
            game = GoGame()
        elif game_type == "gomoku":
            game = GomokuGame()
        else:
            raise ValueError("Unknown game type")
        # 初始化棋盘
        if size is not None:
            if size < 8 or size > 19:
                raise ValueError("Board size must be between 8 and 19")
        from src.game.base_game import GameConfig

        game.start(GameConfig(size=size if size else game.default_size))
        return game

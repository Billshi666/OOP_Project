from src.core.move import Move
from src.core.player import PlayerColor
from src.game.base_game import Game, GameConfig
from src.rules.go_rule import GoRuleEngine


class GoGame(Game):
    def __init__(self, default_size: int = 19):
        super().__init__(default_size=default_size, rule_engine=GoRuleEngine(), name="go")

    def create_move(self, x: int, y: int) -> Move:
        return Move(x=x, y=y, color=self.to_move, is_pass=False)

    def pass_move(self):
        # 围棋允许 pass，沿用基类逻辑
        return super().pass_move()

from src.core.move import Move
from src.core.player import PlayerColor
from src.game.base_game import Game
from src.rules.gomoku_rule import GomokuRuleEngine
from src.rules.base_rule import ApplyResult


class GomokuGame(Game):
    def __init__(self, default_size: int = 15):
        super().__init__(default_size=default_size, rule_engine=GomokuRuleEngine(), name="gomoku")

    def create_move(self, x: int, y: int) -> Move:
        return Move(x=x, y=y, color=self.to_move, is_pass=False)

    def pass_move(self) -> ApplyResult:
        # 五子棋不允许 pass
        return ApplyResult(ended=self.ended, message="Pass not allowed in Gomoku")

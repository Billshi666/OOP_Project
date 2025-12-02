from enum import Enum


class PlayerColor(str, Enum):
    BLACK = "B"
    WHITE = "W"

    def opposite(self) -> "PlayerColor":
        return PlayerColor.BLACK if self == PlayerColor.WHITE else PlayerColor.WHITE

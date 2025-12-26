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
        players = snapshot.get("players") or {}
        legal_moves = snapshot.get("legal_moves") or []
        show_legal_moves = bool(snapshot.get("show_legal_moves", False))
        legal_set = {tuple(m) for m in legal_moves} if show_legal_moves else set()

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
                    row_cells.append("*" if (x, y) in legal_set else "+")
            print(f"{y:2d} " + " ".join(row_cells))

        if players:
            black_entry = players.get(PlayerColor.BLACK.value) or {}
            white_entry = players.get(PlayerColor.WHITE.value) or {}
            black_label = _format_player_entry(black_entry, fallback="Guest")
            white_label = _format_player_entry(white_entry, fallback="Guest")
            print(f"Players: Black={black_label} | White={white_label}")

        if message:
            for line in str(message).splitlines():
                if line.strip() == "":
                    continue
                print(f"[info] {line}")
        if ended:
            if last_result_msg:
                print(f"[result] {last_result_msg}")
            else:
                print("[result] Game ended")
        elif to_move:
            side = "Black" if to_move == PlayerColor.BLACK.value else "White"
            label = (players.get(to_move) or {}).get("label")
            suffix = f" ({label})" if label and label != "Guest" else ""
            print(f"[turn] {side}{suffix} to move")

        if self.show_hint:
            _print_hints(snapshot)


def _format_player_entry(entry: Dict, fallback: str) -> str:
    label = entry.get("label") or fallback
    kind = entry.get("kind")
    if kind == "ai":
        return label
    wins = entry.get("wins")
    games = entry.get("games")
    if label != "Guest" and wins is not None and games is not None:
        return f"{label} ({wins}/{games})"
    return label


def _print_hints(snapshot: Dict) -> None:
    mode = snapshot.get("mode")
    game = snapshot.get("game")
    ended = bool(snapshot.get("ended", False))

    if mode == "replay":
        print("Hints (replay):")
        print("  next | prev | jump n | exit | quit")
        print("  help replay")
        return

    print("Hints:")
    if ended:
        print("  Game ended: save name | replay [name] | start go|gomoku|othello [size] | restart [size]")
    else:
        print("  Play: play x y | undo | resign | restart [size]")
        print("  Save/Load: save name | load [name] | replay [name]")

    print("  Accounts (all games): register/login/logout black|white <username> | who")

    if game == "othello":
        print("  Othello: moves (shows '*' legal) | size must be even 8-18 | forced pass is automatic")
        print("  AI (Othello only): seat black|white ai1|ai2 (AI moves automatically) | seat <side> human to take over")
    elif game == "go":
        print("  Go: pass (go only) | game ends after two consecutive passes")
    elif game == "gomoku":
        print("  Gomoku: pass is not allowed | win by five in a row")

    print("  Help: help [topic]  topics: accounts, ai, othello, replay")
    print("  Hide hints: hint off")

import sys

from src.command_parser import CommandParser
from src.controller import Controller


def main():
    parser = CommandParser()
    controller = Controller()
    print(
        "\n".join(
            [
                "Board Game Platform (Go / Gomoku / Othello)",
                "Type 'help' for full help. Type 'hint off' to hide hints. Type 'quit' to exit.",
                "",
                "Quickstart (Othello + AI):",
                "  start othello 8          # Othello size: even 8-18",
                "  moves                    # show legal moves as '*'",
                "  seat white ai1           # AI is supported only in Othello",
                "  play 2 3",
                "  save game1",
                "  replay game1",
                "",
                "Accounts (all games):",
                "  register black alice     # prompts for password (not echoed)",
                "  login white bob",
                "  who",
                "",
                "Replay mode commands:",
                "  next | prev | jump n | exit",
            ]
        )
    )
    for line in sys.stdin:
        cmd = parser.parse(line)
        if cmd is None:
            continue
        cont = controller.handle(cmd)
        if not cont:
            break


if __name__ == "__main__":
    main()

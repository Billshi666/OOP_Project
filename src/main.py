import sys

from src.command_parser import CommandParser
from src.controller import Controller


def main():
    parser = CommandParser()
    controller = Controller()
    print("Board Game Platform (Go / Gomoku). Type 'start go|gomoku [size]' to begin. 'quit' to exit.")
    for line in sys.stdin:
        cmd = parser.parse(line)
        if cmd is None:
            continue
        cont = controller.handle(cmd)
        if not cont:
            break


if __name__ == "__main__":
    main()

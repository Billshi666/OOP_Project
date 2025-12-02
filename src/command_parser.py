from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Command:
    name: str
    args: List[str]


class CommandParser:
    """
    将用户输入解析为 Command，简单分词，不处理复杂语法。
    """

    def parse(self, raw: str) -> Optional[Command]:
        raw = raw.strip()
        if not raw:
            return None
        parts = raw.split()
        name = parts[0].lower()
        args = parts[1:]
        return Command(name=name, args=args)

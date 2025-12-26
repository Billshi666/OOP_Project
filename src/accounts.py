from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16


@dataclass(frozen=True)
class AccountStats:
    games: int
    wins: int


class AccountManager:
    """
    本地账户管理（注册/登录/战绩），保存于 saves/accounts.json。

    说明：
    - 密码不明文保存，使用 PBKDF2-HMAC-SHA256 + salt；
    - 仅记录：对战场次 games 与胜场 wins，以及与用户关联的录像/存档文件列表 recordings。
    """

    def __init__(self, path: str = os.path.join("saves", "accounts.json")) -> None:
        self.path = path

    # --- public API ---

    def register(self, username: str, password: str) -> None:
        username = self._normalize_username(username)
        if not password:
            raise ValueError("Password must not be empty")

        data = self._load()
        users = data.setdefault("users", {})
        if username in users:
            raise ValueError("Username already exists")

        salt = os.urandom(SALT_BYTES)
        pwd_hash = self._hash_password(password, salt)
        users[username] = {
            "salt": self._b64(salt),
            "hash": self._b64(pwd_hash),
            "games": 0,
            "wins": 0,
            "recordings": [],
        }
        self._save(data)

    def authenticate(self, username: str, password: str) -> bool:
        username = self._normalize_username(username)
        data = self._load()
        user = (data.get("users") or {}).get(username)
        if not user:
            return False
        try:
            salt = self._b64decode(user["salt"])
            expected = self._b64decode(user["hash"])
        except Exception:
            return False
        actual = self._hash_password(password, salt)
        return hmac.compare_digest(expected, actual)

    def get_stats(self, username: str) -> AccountStats:
        username = self._normalize_username(username)
        data = self._load()
        user = (data.get("users") or {}).get(username)
        if not user:
            raise ValueError("Unknown user")
        return AccountStats(games=int(user.get("games", 0)), wins=int(user.get("wins", 0)))

    def add_recording(self, username: str, recording_path: str) -> None:
        username = self._normalize_username(username)
        data = self._load()
        user = (data.get("users") or {}).get(username)
        if not user:
            raise ValueError("Unknown user")
        recordings = user.setdefault("recordings", [])
        if recording_path not in recordings:
            recordings.append(recording_path)
        self._save(data)

    def apply_game_result(self, username: str, won: bool) -> Tuple[int, int]:
        """
        记录一场对局的结果并落盘，返回 (games_inc, wins_inc) 以便回滚。
        """
        username = self._normalize_username(username)
        data = self._load()
        user = (data.get("users") or {}).get(username)
        if not user:
            raise ValueError("Unknown user")
        user["games"] = int(user.get("games", 0)) + 1
        wins_inc = 1 if won else 0
        user["wins"] = int(user.get("wins", 0)) + wins_inc
        self._save(data)
        return 1, wins_inc

    def rollback_game_result(self, username: str, games_inc: int, wins_inc: int) -> None:
        username = self._normalize_username(username)
        data = self._load()
        user = (data.get("users") or {}).get(username)
        if not user:
            return
        user["games"] = max(0, int(user.get("games", 0)) - games_inc)
        user["wins"] = max(0, int(user.get("wins", 0)) - wins_inc)
        self._save(data)

    # --- storage helpers ---

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {"version": 1, "users": {}}
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"version": 1, "users": {}}
        data.setdefault("version", 1)
        data.setdefault("users", {})
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    # --- crypto helpers ---

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)

    def _b64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("ascii")

    def _b64decode(self, data: str) -> bytes:
        return base64.b64decode(data.encode("ascii"))

    def _normalize_username(self, username: str) -> str:
        username = username.strip()
        if not username:
            raise ValueError("Username must not be empty")
        if any(ch.isspace() for ch in username):
            raise ValueError("Username must not contain spaces")
        return username

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "app.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                coin INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                user_id TEXT,
                bet INTEGER,
                numbers TEXT,
                win INTEGER,
                coin_before INTEGER,
                coin_after INTEGER
            )
            """
        )
        conn.commit()


def get_or_create_user(user_id: str, default_coin: int = 1000) -> int:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT coin FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return row["coin"]
        cur.execute(
            "INSERT INTO users (user_id, coin) VALUES (?, ?)",
            (user_id, default_coin),
        )
        conn.commit()
        return default_coin


def set_user_coin(user_id: str, coin: int) -> int:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (user_id, coin)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET coin=excluded.coin
            """,
            (user_id, coin),
        )
        conn.commit()
        return coin


def list_users() -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, coin FROM users ORDER BY user_id")
        return [dict(row) for row in cur.fetchall()]


def reset_all_users(default_coin: int = 1000) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET coin = ?", (default_coin,))
        conn.commit()


def add_history(
    ts: str,
    user_id: str,
    bet: int,
    numbers_json: str,
    win: bool,
    coin_before: int,
    coin_after: int,
) -> None:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO history (ts, user_id, bet, numbers, win, coin_before, coin_after)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, user_id, bet, numbers_json, int(win), coin_before, coin_after),
        )
        conn.commit()


def get_history(user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    query = "SELECT ts, user_id, bet, numbers, win, coin_before, coin_after FROM history"
    params: List[Any] = []
    if user_id:
        query += " WHERE user_id = ?"
        params.append(user_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

    history: List[Dict[str, Any]] = []
    for row in rows:
        numbers = json.loads(row["numbers"]) if row["numbers"] else []
        history.append(
            {
                "ts": row["ts"],
                "user_id": row["user_id"],
                "bet": row["bet"],
                "numbers": numbers,
                "win": bool(row["win"]),
                "coin_before": row["coin_before"],
                "coin_after": row["coin_after"],
            }
        )
    return history

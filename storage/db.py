import sqlite3
import json
from datetime import datetime

DB_PATH = "impactlog.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name like dict
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS standups (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            yesterday   TEXT,
            today       TEXT,
            blockers    TEXT,
            wins        TEXT,
            tags        TEXT,
            raw_input   TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_standup(date: str, yesterday: str, today: str, blockers: str, wins: str, tags: list, raw_input: str):
    conn = get_connection()
    conn.execute("""
        INSERT INTO standups (date, yesterday, today, blockers, wins, tags, raw_input)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, yesterday, today, blockers, wins, json.dumps(tags), raw_input))
    conn.commit()
    conn.close()


def get_standups_for_week(week_start: str, week_end: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM standups
        WHERE date BETWEEN ? AND ?
        ORDER BY date ASC
    """, (week_start, week_end)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_standups() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM standups ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).parent / "autoblog.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS licenses (
                license_key   TEXT PRIMARY KEY,
                plan          TEXT NOT NULL,
                expires_at    TEXT NOT NULL,
                daily_limit   INTEGER NOT NULL DEFAULT 10,
                monthly_limit INTEGER NOT NULL DEFAULT 200,
                status        TEXT NOT NULL DEFAULT 'active',
                note          TEXT,
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS usage_daily (
                license_key TEXT NOT NULL,
                date        TEXT NOT NULL,
                count       INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (license_key, date),
                FOREIGN KEY (license_key) REFERENCES licenses(license_key)
            );

            CREATE TABLE IF NOT EXISTS usage_monthly (
                license_key TEXT NOT NULL,
                year_month  TEXT NOT NULL,
                count       INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (license_key, year_month),
                FOREIGN KEY (license_key) REFERENCES licenses(license_key)
            );

            CREATE TABLE IF NOT EXISTS request_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT,
                endpoint    TEXT NOT NULL,
                model       TEXT,
                success     INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_DB = str(Path(__file__).parent / "autoblog.db")


def _pick_db_path() -> str:
    """Prefer Render persistent disk (/var/data), then DATABASE_PATH, then local file."""
    candidates = ["/var/data/autoblog.db"]
    configured = os.getenv("DATABASE_PATH", "").strip()
    if configured:
        candidates.append(configured)
    candidates.append(_DEFAULT_DB)
    seen = set()
    last_error = None
    for configured_path in candidates:
        if configured_path in seen:
            continue
        seen.add(configured_path)
        path = Path(configured_path).expanduser()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            probe = path.parent / ".autoblog_write_test"
            probe.write_text("ok")
            probe.unlink(missing_ok=True)
            print(f"[AutoBlog] SQLite: {path}", flush=True)
            return str(path)
        except OSError as e:
            last_error = e
            continue
    fallback = Path(_DEFAULT_DB)
    fallback.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"[AutoBlog] DATABASE_PATH unusable ({last_error}); using fallback {fallback}",
        flush=True,
    )
    return str(fallback)


DB_PATH = _pick_db_path()


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


def _ensure_license_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(licenses)")}
    if "started_at" not in cols:
        conn.execute("ALTER TABLE licenses ADD COLUMN started_at TEXT")
    if "duration_days" not in cols:
        conn.execute("ALTER TABLE licenses ADD COLUMN duration_days INTEGER")
    conn.execute(
        """
        UPDATE licenses
        SET started_at = substr(created_at, 1, 10)
        WHERE started_at IS NULL
          AND (duration_days IS NULL OR duration_days = 0)
        """
    )


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
        _ensure_license_columns(conn)

"""라이선스 영속화 — Render 재시작/슬립 후에도 발급 키가 남도록 JSON 금고에 복제한다."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from database import get_db

_REPO_VAULT = Path(__file__).parent / "data" / "licenses.vault.json"


def _vault_paths() -> list[Path]:
    paths: list[Path] = []
    extra = os.getenv("LICENSE_VAULT_PATH", "").strip()
    if extra:
        paths.append(Path(extra).expanduser())
    paths.append(Path("/var/data/licenses.vault.json"))
    paths.append(_REPO_VAULT)
    # unique, keep order
    seen = set()
    out = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _row_to_record(row: Any) -> dict:
    return {
        "license_key": row["license_key"],
        "plan": row["plan"],
        "expires_at": row["expires_at"],
        "daily_limit": row["daily_limit"],
        "monthly_limit": row["monthly_limit"],
        "status": row["status"],
        "note": row["note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def dump_licenses() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM licenses ORDER BY created_at ASC"
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def _load_file(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, dict):
        items = raw.get("licenses") or []
    elif isinstance(raw, list):
        items = raw
    else:
        return []
    out = []
    for item in items:
        if isinstance(item, dict) and item.get("license_key"):
            out.append(item)
    return out


def _merge(records: list[dict]) -> dict[str, dict]:
    """같은 키는 updated_at / expires_at 이 더 최근인 쪽을 유지."""
    merged: dict[str, dict] = {}
    for rec in records:
        key = str(rec.get("license_key") or "").strip()
        if not key:
            continue
        prev = merged.get(key)
        if not prev:
            merged[key] = rec
            continue
        prev_ts = str(prev.get("updated_at") or prev.get("expires_at") or "")
        new_ts = str(rec.get("updated_at") or rec.get("expires_at") or "")
        if new_ts >= prev_ts:
            merged[key] = rec
    return merged


def upsert_records(records: list[dict]) -> int:
    if not records:
        return 0
    count = 0
    with get_db() as conn:
        for rec in records:
            key = str(rec.get("license_key") or "").strip()
            if not key:
                continue
            conn.execute(
                """
                INSERT INTO licenses (
                    license_key, plan, expires_at, daily_limit, monthly_limit,
                    status, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')), COALESCE(?, datetime('now')))
                ON CONFLICT(license_key) DO UPDATE SET
                    plan = excluded.plan,
                    expires_at = excluded.expires_at,
                    daily_limit = excluded.daily_limit,
                    monthly_limit = excluded.monthly_limit,
                    status = excluded.status,
                    note = COALESCE(excluded.note, licenses.note),
                    updated_at = datetime('now')
                """,
                (
                    key,
                    rec.get("plan") or "paid",
                    rec.get("expires_at") or "2099-12-31",
                    int(rec.get("daily_limit") or 3),
                    int(rec.get("monthly_limit") or 90),
                    rec.get("status") or "active",
                    rec.get("note"),
                    rec.get("created_at"),
                    rec.get("updated_at"),
                ),
            )
            count += 1
    return count


def persist_vault() -> None:
    payload = {
        "version": 1,
        "licenses": dump_licenses(),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    for path in _vault_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            print(f"[AutoBlog] vault write skipped ({path}): {e}", flush=True)


def restore_vault() -> int:
    collected: list[dict] = []
    for path in _vault_paths():
        loaded = _load_file(path)
        if loaded:
            print(f"[AutoBlog] vault loaded {len(loaded)} keys from {path}", flush=True)
            collected.extend(loaded)
    extra_json = os.getenv("LICENSE_VAULT_JSON", "").strip()
    if extra_json:
        try:
            raw = json.loads(extra_json)
            if isinstance(raw, dict):
                collected.extend(raw.get("licenses") or [])
            elif isinstance(raw, list):
                collected.extend(raw)
        except json.JSONDecodeError:
            print("[AutoBlog] LICENSE_VAULT_JSON parse failed", flush=True)
    merged = _merge(collected)
    n = upsert_records(list(merged.values()))
    if n:
        persist_vault()
        print(f"[AutoBlog] restored {n} license(s) from vault", flush=True)
    return n

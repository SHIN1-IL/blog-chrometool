import secrets
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from database import get_db

KST = ZoneInfo("Asia/Seoul")

PLAN_DEFAULTS = {
    "paid": {"daily_limit": 10, "monthly_limit": 200},
    "family_free": {"daily_limit": 10, "monthly_limit": 150},
    "demo": {"daily_limit": 3, "monthly_limit": 10},
}


@dataclass
class LicenseStatus:
    valid: bool
    message: str = ""
    remaining_days: int = 0
    expires: str = ""
    plan: str = ""
    daily_used: int = 0
    daily_limit: int = 0
    monthly_used: int = 0
    monthly_limit: int = 0


def today_kst() -> date:
    return datetime.now(KST).date()


def year_month_kst() -> str:
    d = today_kst()
    return f"{d.year:04d}-{d.month:02d}"


def generate_license_key() -> str:
    chars = string.ascii_uppercase + string.digits
    parts = [
        "".join(secrets.choice(chars) for _ in range(4))
        for _ in range(3)
    ]
    return "-".join(parts)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _get_usage(license_key: str) -> tuple[int, int]:
    today = today_kst().isoformat()
    ym = year_month_kst()
    with get_db() as conn:
        daily_row = conn.execute(
            "SELECT count FROM usage_daily WHERE license_key = ? AND date = ?",
            (license_key, today),
        ).fetchone()
        monthly_row = conn.execute(
            "SELECT count FROM usage_monthly WHERE license_key = ? AND year_month = ?",
            (license_key, ym),
        ).fetchone()
    daily_used = daily_row["count"] if daily_row else 0
    monthly_used = monthly_row["count"] if monthly_row else 0
    return daily_used, monthly_used


def get_license(license_key: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM licenses WHERE license_key = ?",
            (license_key,),
        ).fetchone()
    return dict(row) if row else None


def check_license(license_key: str) -> LicenseStatus:
    lic = get_license(license_key)
    if not lic:
        return LicenseStatus(valid=False, message="등록되지 않았거나 만료된 라이선스입니다.")

    if lic["status"] == "suspended":
        return LicenseStatus(valid=False, message="정지된 라이선스입니다. 문의해 주세요.")

    expire_date = _parse_date(lic["expires_at"])
    remaining = (expire_date - today_kst()).days
    if remaining < 0:
        return LicenseStatus(valid=False, message="등록되지 않았거나 만료된 라이선스입니다.")

    daily_used, monthly_used = _get_usage(license_key)
    return LicenseStatus(
        valid=True,
        remaining_days=remaining,
        expires=lic["expires_at"],
        plan=lic["plan"],
        daily_used=daily_used,
        daily_limit=lic["daily_limit"],
        monthly_used=monthly_used,
        monthly_limit=lic["monthly_limit"],
    )


def check_quota(license_key: str) -> LicenseStatus:
    status = check_license(license_key)
    if not status.valid:
        return status

    if status.daily_used >= status.daily_limit:
        return LicenseStatus(
            valid=False,
            message=f"오늘 생성 한도({status.daily_limit}건)를 모두 사용했습니다. 내일 다시 이용 가능합니다.",
            remaining_days=status.remaining_days,
            expires=status.expires,
            plan=status.plan,
            daily_used=status.daily_used,
            daily_limit=status.daily_limit,
            monthly_used=status.monthly_used,
            monthly_limit=status.monthly_limit,
        )

    if status.monthly_used >= status.monthly_limit:
        return LicenseStatus(
            valid=False,
            message=f"이번 달 생성 한도({status.monthly_limit}건)를 모두 사용했습니다.",
            remaining_days=status.remaining_days,
            expires=status.expires,
            plan=status.plan,
            daily_used=status.daily_used,
            daily_limit=status.daily_limit,
            monthly_used=status.monthly_used,
            monthly_limit=status.monthly_limit,
        )

    return status


def increment_usage(license_key: str) -> None:
    today = today_kst().isoformat()
    ym = year_month_kst()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO usage_daily (license_key, date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(license_key, date) DO UPDATE SET count = count + 1
            """,
            (license_key, today),
        )
        conn.execute(
            """
            INSERT INTO usage_monthly (license_key, year_month, count)
            VALUES (?, ?, 1)
            ON CONFLICT(license_key, year_month) DO UPDATE SET count = count + 1
            """,
            (license_key, ym),
        )


def log_request(
    license_key: str,
    endpoint: str,
    model: Optional[str] = None,
    success: bool = True,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO request_logs (license_key, endpoint, model, success)
            VALUES (?, ?, ?, ?)
            """,
            (license_key, endpoint, model, 1 if success else 0),
        )


def create_license(
    plan: str,
    days: int = 0,
    months: int = 0,
    license_key: Optional[str] = None,
    note: Optional[str] = None,
    daily_limit: Optional[int] = None,
    monthly_limit: Optional[int] = None,
) -> dict:
    if plan not in PLAN_DEFAULTS:
        raise ValueError(f"Unknown plan: {plan}. Use: {', '.join(PLAN_DEFAULTS)}")

    if days <= 0 and months <= 0:
        raise ValueError("days or months must be positive")

    total_days = days + months * 30
    expires_at = (today_kst() + timedelta(days=total_days)).isoformat()
    defaults = PLAN_DEFAULTS[plan]

    key = license_key or generate_license_key()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO licenses (
                license_key, plan, expires_at, daily_limit, monthly_limit, note
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                plan,
                expires_at,
                daily_limit if daily_limit is not None else defaults["daily_limit"],
                monthly_limit if monthly_limit is not None else defaults["monthly_limit"],
                note,
            ),
        )

    return get_license(key)


def extend_license(license_key: str, days: int) -> dict:
    lic = get_license(license_key)
    if not lic:
        raise ValueError(f"License not found: {license_key}")

    current_expire = _parse_date(lic["expires_at"])
    base = max(current_expire, today_kst())
    new_expire = (base + timedelta(days=days)).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            UPDATE licenses
            SET expires_at = ?, status = 'active', updated_at = datetime('now')
            WHERE license_key = ?
            """,
            (new_expire, license_key),
        )

    return get_license(license_key)


def suspend_license(license_key: str) -> dict:
    lic = get_license(license_key)
    if not lic:
        raise ValueError(f"License not found: {license_key}")

    with get_db() as conn:
        conn.execute(
            """
            UPDATE licenses
            SET status = 'suspended', updated_at = datetime('now')
            WHERE license_key = ?
            """,
            (license_key,),
        )

    return get_license(license_key)


def activate_license(license_key: str) -> dict:
    lic = get_license(license_key)
    if not lic:
        raise ValueError(f"License not found: {license_key}")

    with get_db() as conn:
        conn.execute(
            """
            UPDATE licenses
            SET status = 'active', updated_at = datetime('now')
            WHERE license_key = ?
            """,
            (license_key,),
        )

    return get_license(license_key)


def set_limits(
    license_key: str,
    daily_limit: Optional[int] = None,
    monthly_limit: Optional[int] = None,
) -> dict:
    lic = get_license(license_key)
    if not lic:
        raise ValueError(f"License not found: {license_key}")

    updates = []
    params = []
    if daily_limit is not None:
        updates.append("daily_limit = ?")
        params.append(daily_limit)
    if monthly_limit is not None:
        updates.append("monthly_limit = ?")
        params.append(monthly_limit)

    if not updates:
        raise ValueError("At least one of daily_limit or monthly_limit is required")

    updates.append("updated_at = datetime('now')")
    params.append(license_key)

    with get_db() as conn:
        conn.execute(
            f"UPDATE licenses SET {', '.join(updates)} WHERE license_key = ?",
            params,
        )

    return get_license(license_key)


def list_licenses() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM licenses ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def seed_demo_key() -> None:
    if get_license("DEMO-KEY"):
        return
    create_license(
        plan="demo",
        days=365,
        license_key="DEMO-KEY",
        note="개발·체험용 데모 키",
    )

import secrets
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from database import get_db

KST = ZoneInfo("Asia/Seoul")

# 체험: 총 1건 후 종료 / 지인: 일1·월30·1달 / 유료: 일3·월90 / 관리자: 일3·월무제한
PLAN_DEFAULTS = {
    "trial": {"daily_limit": 1, "monthly_limit": 1},
    "family_free": {"daily_limit": 1, "monthly_limit": 30},
    "paid": {"daily_limit": 3, "monthly_limit": 90},
    "admin_test": {"daily_limit": 3, "monthly_limit": 999999},
    # 하위 호환 (구 DEMO-KEY)
    "demo": {"daily_limit": 1, "monthly_limit": 1},
}

PLAN_LABELS = {
    "trial": "체험플랜",
    "family_free": "지인플랜",
    "paid": "유료플랜",
    "admin_test": "관리자테스트",
    "demo": "체험플랜",
}

ADMIN_TEST_KEY = "ADMIN-TEST"


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


def plan_label(plan: str) -> str:
    return PLAN_LABELS.get(plan, plan)


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

    if lic["status"] == "exhausted":
        return LicenseStatus(
            valid=False,
            message="체험이 종료되었습니다. 1건 사용을 모두 완료했습니다.",
            plan=lic["plan"],
        )

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
        msg = f"이번 달 생성 한도({status.monthly_limit}건)를 모두 사용했습니다."
        if status.plan in ("trial", "demo"):
            msg = "체험이 종료되었습니다. 1건 사용을 모두 완료했습니다."
        return LicenseStatus(
            valid=False,
            message=msg,
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


def mark_trial_exhausted(license_key: str) -> None:
    """체험/구데모 키: 1건 사용 후 종료."""
    lic = get_license(license_key)
    if not lic or lic["plan"] not in ("trial", "demo"):
        return
    with get_db() as conn:
        conn.execute(
            """
            UPDATE licenses
            SET status = 'exhausted', updated_at = datetime('now')
            WHERE license_key = ?
            """,
            (license_key,),
        )
    _persist_vault()


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

    lic = get_license(key)
    _persist_vault()
    return lic


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

    lic = get_license(license_key)
    _persist_vault()
    return lic


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

    lic = get_license(license_key)
    _persist_vault()
    return lic


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

    lic = get_license(license_key)
    _persist_vault()
    return lic


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

    lic = get_license(license_key)
    _persist_vault()
    return lic


def list_licenses() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM licenses ORDER BY created_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        daily_used, monthly_used = _get_usage(item["license_key"])
        item["daily_used"] = daily_used
        item["monthly_used"] = monthly_used
        item["plan_label"] = plan_label(item.get("plan") or "")
        out.append(item)
    return out


def seed_admin_test_key() -> None:
    """관리자 고정 키 ADMIN-TEST (일 3 · 월 무제한)."""
    if get_license(ADMIN_TEST_KEY):
        # 기존 키가 있으면 한도·플랜을 관리자 설정으로 맞춤
        defaults = PLAN_DEFAULTS["admin_test"]
        with get_db() as conn:
            conn.execute(
                """
                UPDATE licenses
                SET plan = 'admin_test',
                    daily_limit = ?,
                    monthly_limit = ?,
                    status = 'active',
                    updated_at = datetime('now')
                WHERE license_key = ?
                """,
                (defaults["daily_limit"], defaults["monthly_limit"], ADMIN_TEST_KEY),
            )
        _persist_vault()
        return
    create_license(
        plan="admin_test",
        days=3650,
        license_key=ADMIN_TEST_KEY,
        note="관리자 테스트 고정 키",
    )


def seed_demo_key() -> None:
    """하위 호환: 예전 호출명 → 관리자 키 시드."""
    seed_admin_test_key()


def _persist_vault() -> None:
    try:
        from license_vault import persist_vault

        persist_vault()
    except Exception as e:
        print(f"[AutoBlog] vault persist failed: {e}", flush=True)

#!/usr/bin/env python3
"""AutoBlog AI — 라이선스 관리 CLI"""

import argparse
import sys

from database import init_db
from license_service import (
    ADMIN_TEST_KEY,
    activate_license,
    create_license,
    extend_license,
    get_license,
    list_licenses,
    set_limits,
    suspend_license,
    seed_admin_test_key,
)


def cmd_create(args: argparse.Namespace) -> None:
    lic = create_license(
        plan=args.plan,
        days=args.days or 0,
        months=args.months or 0,
        license_key=args.key,
        note=args.note,
        daily_limit=args.daily,
        monthly_limit=args.monthly,
    )
    print("✅ 라이선스 생성 완료")
    print(f"   키: {lic['license_key']}")
    print(f"   플랜: {lic['plan']}")
    print(f"   만료: {lic['expires_at']}")
    print(f"   한도: 일 {lic['daily_limit']} / 월 {lic['monthly_limit']}")
    if lic.get("note"):
        print(f"   메모: {lic['note']}")


def cmd_extend(args: argparse.Namespace) -> None:
    lic = extend_license(args.key, args.days)
    print(f"✅ 연장 완료: {lic['license_key']} → 만료 {lic['expires_at']}")


def cmd_suspend(args: argparse.Namespace) -> None:
    lic = suspend_license(args.key)
    print(f"⛔ 정지 완료: {lic['license_key']}")


def cmd_activate(args: argparse.Namespace) -> None:
    lic = activate_license(args.key)
    print(f"✅ 활성화 완료: {lic['license_key']}")


def cmd_set_limit(args: argparse.Namespace) -> None:
    lic = set_limits(args.key, daily_limit=args.daily, monthly_limit=args.monthly)
    print(f"✅ 한도 변경: {lic['license_key']} → 일 {lic['daily_limit']} / 월 {lic['monthly_limit']}")


def cmd_show(args: argparse.Namespace) -> None:
    lic = get_license(args.key)
    if not lic:
        print(f"❌ 라이선스 없음: {args.key}")
        sys.exit(1)
    for k, v in lic.items():
        print(f"  {k}: {v}")


def cmd_list(_: argparse.Namespace) -> None:
    licenses = list_licenses()
    if not licenses:
        print("등록된 라이선스가 없습니다.")
        return
    print(f"{'키':<20} {'플랜':<14} {'만료':<12} {'상태':<10} {'일한도':<6} {'메모'}")
    print("-" * 80)
    for lic in licenses:
        print(
            f"{lic['license_key']:<20} "
            f"{lic['plan']:<14} "
            f"{lic['expires_at']:<12} "
            f"{lic['status']:<10} "
            f"{lic['daily_limit']:<6} "
            f"{lic.get('note') or ''}"
        )


def cmd_seed(_: argparse.Namespace) -> None:
    seed_admin_test_key()
    print(f"✅ {ADMIN_TEST_KEY} 시드 완료 (관리자테스트 · 일3 · 월무제한)")


def main() -> None:
    init_db()

    parser = argparse.ArgumentParser(description="AutoBlog AI 라이선스 관리")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="새 라이선스 발급")
    p_create.add_argument(
        "--plan",
        required=True,
        choices=["paid", "family_free", "trial", "admin_test", "demo"],
    )
    p_create.add_argument("--days", type=int, default=0)
    p_create.add_argument("--months", type=int, default=0)
    p_create.add_argument("--key", help="지정 키 (미지정 시 자동 생성)")
    p_create.add_argument("--note", default="")
    p_create.add_argument("--daily", type=int)
    p_create.add_argument("--monthly", type=int)
    p_create.set_defaults(func=cmd_create)

    p_extend = sub.add_parser("extend", help="만료일 연장")
    p_extend.add_argument("--key", required=True)
    p_extend.add_argument("--days", type=int, required=True)
    p_extend.set_defaults(func=cmd_extend)

    p_suspend = sub.add_parser("suspend", help="라이선스 정지")
    p_suspend.add_argument("--key", required=True)
    p_suspend.set_defaults(func=cmd_suspend)

    p_activate = sub.add_parser("activate", help="라이선스 재활성화")
    p_activate.add_argument("--key", required=True)
    p_activate.set_defaults(func=cmd_activate)

    p_limit = sub.add_parser("set-limit", help="일/월 한도 변경")
    p_limit.add_argument("--key", required=True)
    p_limit.add_argument("--daily", type=int)
    p_limit.add_argument("--monthly", type=int)
    p_limit.set_defaults(func=cmd_set_limit)

    p_show = sub.add_parser("show", help="라이선스 상세 조회")
    p_show.add_argument("--key", required=True)
    p_show.set_defaults(func=cmd_show)

    p_list = sub.add_parser("list", help="전체 라이선스 목록")
    p_list.set_defaults(func=cmd_list)

    p_seed = sub.add_parser("seed", help=f"{ADMIN_TEST_KEY} 관리자 키 시드")
    p_seed.set_defaults(func=cmd_seed)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

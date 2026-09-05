import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from license_service import (
    activate_license,
    create_license,
    extend_license,
    get_license,
    list_licenses,
    set_limits,
    suspend_license,
)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Admin API가 비활성화되어 있습니다. ADMIN_TOKEN 환경변수를 설정하세요.",
        )
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="인증 실패")


class AdminCreateRequest(BaseModel):
    plan: str = Field(pattern="^(paid|family_free|trial|admin_test|demo)$")
    days: int = 0
    months: int = 0
    license_key: Optional[str] = None
    note: str = ""
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None


class AdminExtendRequest(BaseModel):
    days: int = Field(gt=0)


class AdminSetLimitRequest(BaseModel):
    daily_limit: Optional[int] = Field(default=None, gt=0)
    monthly_limit: Optional[int] = Field(default=None, gt=0)


@router.get("/licenses", dependencies=[Depends(require_admin)])
def admin_list_licenses():
    return {"licenses": list_licenses()}


@router.get("/licenses/{license_key}", dependencies=[Depends(require_admin)])
def admin_get_license(license_key: str):
    lic = get_license(license_key)
    if not lic:
        raise HTTPException(status_code=404, detail="라이선스를 찾을 수 없습니다.")
    return lic


@router.post("/licenses", dependencies=[Depends(require_admin)])
def admin_create_license(req: AdminCreateRequest):
    try:
        lic = create_license(
            plan=req.plan,
            days=req.days,
            months=req.months,
            license_key=req.license_key,
            note=req.note or None,
            daily_limit=req.daily_limit,
            monthly_limit=req.monthly_limit,
        )
        return lic
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/licenses/{license_key}/extend", dependencies=[Depends(require_admin)])
def admin_extend_license(license_key: str, req: AdminExtendRequest):
    try:
        return extend_license(license_key, req.days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/licenses/{license_key}/suspend", dependencies=[Depends(require_admin)])
def admin_suspend_license(license_key: str):
    try:
        return suspend_license(license_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/licenses/{license_key}/activate", dependencies=[Depends(require_admin)])
def admin_activate_license(license_key: str):
    try:
        return activate_license(license_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/licenses/{license_key}/limits", dependencies=[Depends(require_admin)])
def admin_set_limits(license_key: str, req: AdminSetLimitRequest):
    try:
        return set_limits(
            license_key,
            daily_limit=req.daily_limit,
            monthly_limit=req.monthly_limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

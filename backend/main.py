from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

import env_loader  # noqa: F401
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_service import (
    build_prompt,
    channels_to_legacy_result,
    generate_channels,
)
from admin_routes import router as admin_router
from business_config import get_business_info
from database import init_db
from license_service import (
    check_license,
    increment_usage,
    log_request,
    mark_trial_exhausted,
    plan_label,
    seed_admin_test_key,
)

WEB_DIR = Path(__file__).parent / "web"
OPS_DIR = Path(__file__).parent / "ops"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_admin_test_key()
    yield


app = FastAPI(title="AutoBlog AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


class LicenseCheckRequest(BaseModel):
    license_key: str


class GenerateRequest(BaseModel):
    license_key: str
    biz_type: str = "plumbing"
    company_name: str = ""
    order_detail: str = ""
    location: str = Field(min_length=1)
    customer_impression: str = ""
    weather: str = ""
    issue: str = Field(min_length=1)  # 해결사항
    obstacles: List[str] = []
    process: str = ""  # 해결과정
    equipment: str = ""  # 사용장비
    solution: str = ""  # 하위 호환 (장비+공정 합침)
    customer_reaction: str = ""
    feeling: str = ""  # 완료기분
    extra: str = ""  # 기타사항
    tone: str = Field(min_length=1)
    photo_count: int = Field(default=3, ge=0, le=10)
    video_count: int = Field(default=0, ge=0, le=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/business")
def business():
    return get_business_info()


@app.get("/")
def root():
    return RedirectResponse(url="/app/")


@app.get("/ops")
def ops_redirect():
    return RedirectResponse(url="/ops/")


def _status_payload(status) -> dict:
    daily_remaining = max(0, status.daily_limit - status.daily_used)
    monthly_remaining = max(0, status.monthly_limit - status.monthly_used)
    unlimited_monthly = status.monthly_limit >= 999999
    return {
        "valid": True,
        "remaining_days": status.remaining_days,
        "expires": status.expires,
        "plan": status.plan,
        "plan_label": plan_label(status.plan),
        "daily_used": status.daily_used,
        "daily_limit": status.daily_limit,
        "daily_remaining": daily_remaining,
        "monthly_used": status.monthly_used,
        "monthly_limit": status.monthly_limit,
        "monthly_remaining": None if unlimited_monthly else monthly_remaining,
        "monthly_unlimited": unlimited_monthly,
    }


@app.post("/api/license/verify")
def verify_license(req: LicenseCheckRequest):
    status = check_license(req.license_key.strip())
    if not status.valid:
        return {"valid": False, "message": status.message, "plan": status.plan or ""}
    return _status_payload(status)


@app.post("/api/generate")
def generate_post(req: GenerateRequest):
    key = req.license_key.strip()
    status = check_license(key)

    if not status.valid:
        raise HTTPException(status_code=403, detail=status.message)

    if status.daily_used >= status.daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"오늘 생성 한도({status.daily_limit}건)를 모두 사용했습니다. 내일 다시 이용 가능합니다.",
        )

    if status.monthly_used >= status.monthly_limit:
        detail = f"이번 달 생성 한도({status.monthly_limit}건)를 모두 사용했습니다."
        if status.plan in ("trial", "demo"):
            detail = "체험이 종료되었습니다. 1건 사용을 모두 완료했습니다."
        raise HTTPException(status_code=429, detail=detail)

    process = (req.process or "").strip()
    equipment = (req.equipment or "").strip()
    solution = (req.solution or "").strip()
    if not solution:
        parts = [p for p in (process, equipment) if p]
        solution = " / ".join(parts)
    if not solution:
        raise HTTPException(status_code=422, detail="해결과정 또는 사용장비를 입력해 주세요.")

    prompt = build_prompt(
        biz_type=req.biz_type,
        company_name=req.company_name,
        order_detail=req.order_detail,
        location=req.location,
        customer_impression=req.customer_impression,
        weather=req.weather,
        issue=req.issue,
        obstacles=req.obstacles,
        process=process,
        equipment=equipment,
        solution=solution,
        customer_reaction=req.customer_reaction,
        feeling=req.feeling,
        extra=req.extra,
        tone=req.tone,
        photo_count=req.photo_count,
        video_count=req.video_count,
    )

    model = ""
    try:
        channels, model = generate_channels(prompt)
        increment_usage(key)
        mark_trial_exhausted(key)
        log_request(key, "/api/generate", model=model, success=True)
        return {
            **channels,
            "result": channels_to_legacy_result(channels),
            "model": model,
            "remaining_days": status.remaining_days,
        }
    except Exception as e:
        log_request(key, "/api/generate", model=model or None, success=False)
        message = str(e)
        low = message.lower()
        if "openai" in low and (
            "credit" in low or "insufficient" in low or "openai http 429" in low
        ):
            if "timeout" in low or "gemini" in low:
                detail = "Gemini 응답이 오래 걸렸고, 예비 엔진(OpenAI)은 잔액이 없습니다. 잠시 후 다시 시도해 주세요."
            else:
                detail = "예비 엔진(OpenAI) 잔액이 없습니다. platform.openai.com에서 크레딧을 충전하거나 Gemini만 사용하세요."
        elif "401" in message or "API_KEY_INVALID" in message or "API key" in message:
            detail = "Gemini API 키가 올바르지 않습니다. Google AI Studio에서 키 다시 발급해 .env에 넣어 주세요."
        elif "404" in message or "not found" in message.lower() or "no longer available" in message.lower():
            detail = "Gemini 모델 이름을 찾지 못했습니다. 서버 터미널의 Gemini 로그를 확인해 주세요."
        elif "timeout" in low or "timed out" in low:
            detail = "Gemini가 시간 안에 글을 끝내지 못했습니다. 1분 뒤 한 번만 다시 눌러 주세요. (OpenAI 잔액이 없어 예비 엔진은 건너뜁니다)"
        elif "429" in message or "quota" in low:
            detail = "AI 사용 한도 문제입니다. Gemini는 AI Studio, 예비 엔진은 OpenAI 결제 화면을 확인해 주세요."
        else:
            detail = "글 생성에 실패했습니다. 서버 터미널의 Gemini 로그를 확인해 주세요."
        raise HTTPException(status_code=500, detail=detail) from e


app.mount("/ops", StaticFiles(directory=str(OPS_DIR), html=True), name="ops")
app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

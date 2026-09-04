from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

import env_loader  # noqa: F401
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_service import build_prompt, generate_content
from admin_routes import router as admin_router
from business_config import get_business_info
from database import init_db
from license_service import (
    check_license,
    increment_usage,
    log_request,
    seed_demo_key,
)

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_demo_key()
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
    location: str = Field(min_length=1)
    weather: str = ""
    issue: str = Field(min_length=1)
    obstacles: List[str] = []
    solution: str = Field(min_length=1)
    feeling: str = ""
    tone: str = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/business")
def business():
    return get_business_info()


@app.get("/")
def root():
    return RedirectResponse(url="/app/")


@app.post("/api/license/verify")
def verify_license(req: LicenseCheckRequest):
    status = check_license(req.license_key.strip())
    if not status.valid:
        return {"valid": False, "message": status.message}
    return {
        "valid": True,
        "remaining_days": status.remaining_days,
        "expires": status.expires,
        "plan": status.plan,
        "daily_used": status.daily_used,
        "daily_limit": status.daily_limit,
        "monthly_used": status.monthly_used,
        "monthly_limit": status.monthly_limit,
    }


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
        raise HTTPException(
            status_code=429,
            detail=f"이번 달 생성 한도({status.monthly_limit}건)를 모두 사용했습니다.",
        )

    prompt = build_prompt(
        location=req.location,
        weather=req.weather,
        issue=req.issue,
        obstacles=req.obstacles,
        solution=req.solution,
        feeling=req.feeling,
        tone=req.tone,
    )

    model = ""
    try:
        content, model = generate_content(prompt)
        increment_usage(key)
        log_request(key, "/api/generate", model=model, success=True)
        return {"result": content, "model": model}
    except Exception as e:
        log_request(key, "/api/generate", model=model or None, success=False)
        message = str(e)
        if "401" in message or "API_KEY_INVALID" in message or "API key" in message:
            detail = "Gemini API 키가 올바르지 않습니다. Google AI Studio에서 키를 다시 발급해 .env에 넣어 주세요."
        elif "404" in message or "not found" in message.lower() or "no longer available" in message.lower():
            detail = "Gemini 모델 이름을 찾지 못했습니다. 서버 터미널의 Gemini 로그를 확인해 주세요."
        elif "429" in message or "quota" in message.lower():
            detail = "AI 사용 한도 문제입니다. Google AI Studio 사용량/결제를 확인해 주세요."
        elif "timeout" in message.lower():
            detail = "AI 응답이 지연되었습니다. 잠시 후 다시 눌러 주세요."
        else:
            detail = "글 생성에 실패했습니다. 서버 터미널의 Gemini 로그를 확인해 주세요."
        raise HTTPException(status_code=500, detail=detail) from e


app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

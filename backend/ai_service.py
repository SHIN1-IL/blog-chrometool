import logging
import os
from typing import List

import requests

import env_loader  # noqa: F401

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _gemini_timeout() -> float:
    return float(os.getenv("GEMINI_TIMEOUT", "20"))


def _openai_timeout() -> float:
    return float(os.getenv("OPENAI_TIMEOUT", "45"))


def _max_tokens() -> int:
    return int(os.getenv("MAX_OUTPUT_TOKENS", "3000"))


def build_prompt(
    location: str,
    weather: str,
    issue: str,
    obstacles: List[str],
    solution: str,
    feeling: str,
    tone: str,
) -> str:
    obstacles_text = ", ".join(obstacles) if obstacles else "없음"
    return f"""당신은 네이버 블로그 로컬 상위노출 전문 시공 마케터입니다.
현장 사장님이 직접 겪은 사실만을 바탕으로 신뢰도 높은 후기 글을 작성하세요.

[현장 팩트]
- 작업 위치: {location}
- 당일 날씨: {weather or "미기재"}
- 접수된 고장/문제: {issue}
- 현장 돌발상황: {obstacles_text}
- 해결 장비 및 공정: {solution}
- 사장님 소감: {feeling or "미기재"}
- 문체 톤: {tone}

[작성 가이드]
1. 제목: [지역명 + 핵심 작업 내용 + 결과] 구조로 1줄 작성.
2. 서두: 날씨와 함께 방문 계기를 친근하게 설명.
3. 본문: 독자가 신뢰할 수 있게 작업 순서대로 설명하며 중간에 [현장 사진 1: 점검], [현장 사진 2: 작업 중], [현장 사진 3: 완료] 표시를 삽입.
4. 네이버 알고리즘 저품질 방지를 위해 사장님의 감정과 실제 겪은 고충을 진솔하게 반영.
5. 하단: 추천 검색 태그 10개 나열.

출력 형태 (반드시 이 구분자를 사용):
[제목]
...
[본문]
...
[태그]
...
"""


def _http_error_message(res: requests.Response) -> str:
    try:
        data = res.json()
        err = data.get("error", {})
        if isinstance(err, dict):
            return str(err.get("message") or data)
        return str(data.get("error") or data)
    except Exception:
        return res.text[:200]


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("empty candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = []
    for part in parts:
        if part.get("thought"):
            continue
        text = part.get("text")
        if text:
            texts.append(text)
    if not texts:
        raise RuntimeError("empty content")
    return "\n".join(texts)


def _call_gemini(prompt: str) -> tuple[str, str]:
    key = _gemini_key()
    if not key or key == "your_gemini_key":
        raise RuntimeError("GEMINI_API_KEY not configured")

    last_error = None
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key,
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": _max_tokens(),
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    for model in GEMINI_MODELS:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        try:
            res = requests.post(
                url, json=payload, headers=headers, timeout=_gemini_timeout()
            )
            if not res.ok:
                last_error = RuntimeError(
                    f"Gemini {model} HTTP {res.status_code}: {_http_error_message(res)}"
                )
                logger.warning("%s", last_error)
                continue
            return _extract_text(res.json()), model
        except requests.Timeout:
            last_error = RuntimeError(f"Gemini {model} timeout")
            logger.warning("%s", last_error)
        except Exception as e:
            last_error = e
            logger.warning("Gemini %s error: %s", model, e)
    raise last_error or RuntimeError("Gemini failed")


def _call_openai(prompt: str) -> str:
    key = _openai_key()
    if not key or key == "your_openai_key":
        raise RuntimeError("OPENAI_API_KEY not configured")

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "당신은 네이버 블로그 현장 시공 전문 작가입니다.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": _max_tokens(),
    }
    headers = {"Authorization": f"Bearer {key}"}
    res = requests.post(
        OPENAI_URL, json=payload, headers=headers, timeout=_openai_timeout()
    )
    if not res.ok:
        raise RuntimeError(f"OpenAI HTTP {res.status_code}: {_http_error_message(res)}")
    data = res.json()
    return data["choices"][0]["message"]["content"]


def generate_content(prompt: str) -> tuple[str, str]:
    """Returns (content, model_name). Raises on total failure."""
    openai_enabled = os.getenv("OPENAI_ENABLED", "false").lower() in ("1", "true", "yes")
    try:
        content, model = _call_gemini(prompt)
        return content, model
    except Exception as e:
        if not openai_enabled:
            raise
        logger.warning("[Fallback] Gemini failed (%s) -> GPT-4o-mini", e)
        try:
            content = _call_openai(prompt)
            return content, "gpt-4o-mini"
        except Exception as oe:
            logger.error("OpenAI fallback failed: %s", oe)
            raise RuntimeError(f"Gemini: {e} / OpenAI: {oe}") from oe

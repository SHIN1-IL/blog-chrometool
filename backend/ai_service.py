import json
import logging
import os
import re
from typing import Any, List

import requests

import env_loader  # noqa: F401

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
]
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini"

JSON_SYSTEM = (
    "당신은 현장 시공 사장님의 로컬 마케팅 카피라이터입니다. "
    "반드시 유효한 JSON만 출력하고 마크다운 코드펜스·설명을 넣지 마세요. "
    "입력에 없는 자재·자격·할인을 지어내지 마세요."
)

BIZ_TYPE_LABELS = {
    "plumbing": "설비업체",
    "cleaning": "청소업체",
    "custom": "자가입력",
}


def _gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _gemini_timeout() -> float:
    return float(os.getenv("GEMINI_TIMEOUT", "60"))


def _openai_timeout() -> float:
    return float(os.getenv("OPENAI_TIMEOUT", "45"))


def _max_tokens() -> int:
    return int(os.getenv("MAX_OUTPUT_TOKENS", "4000"))


def _openai_enabled() -> bool:
    flag = os.getenv("OPENAI_ENABLED", "").strip().lower()
    if flag in ("0", "false", "no"):
        return False
    if flag in ("1", "true", "yes"):
        return True
    key = _openai_key()
    return bool(key) and key != "your_openai_key"


def _clamp_photo(n: int) -> int:
    try:
        return max(0, min(5, int(n)))
    except (TypeError, ValueError):
        return 3


def _clamp_video(n: int) -> int:
    try:
        return max(0, min(1, int(n)))
    except (TypeError, ValueError):
        return 0


def _media_instructions(photo_count: int, video_count: int) -> str:
    lines = []
    if photo_count <= 0:
        lines.append("- 사진 자리표시([현장 사진])를 넣지 마세요.")
    else:
        kinds = ["점검", "작업 중", "완료", "자재/장비", "주변 정리"]
        markers = [
            f"[현장 사진 {i + 1}: {kinds[i] if i < len(kinds) else '추가'}]"
            for i in range(photo_count)
        ]
        lines.append(
            "- 블로그 본문에 아래 사진 마커를 작업 흐름에 맞게 정확히 "
            f"{photo_count}개만 삽입: " + ", ".join(markers)
        )
    if video_count <= 0:
        lines.append("- 영상 자리표시를 넣지 마세요.")
    else:
        lines.append(
            "- 블로그 본문에 [현장 영상 1: 작업 전→후 15초] 를 1개만 넣으세요. "
            "파일은 사장님이 직접 첨부합니다."
        )
    return "\n".join(lines)


def build_prompt(
    location: str,
    weather: str,
    issue: str,
    obstacles: List[str],
    solution: str,
    feeling: str,
    tone: str,
    biz_type: str = "plumbing",
    company_name: str = "",
    order_detail: str = "",
    customer_impression: str = "",
    process: str = "",
    equipment: str = "",
    customer_reaction: str = "",
    extra: str = "",
    photo_count: int = 3,
    video_count: int = 0,
) -> str:
    photo_count = _clamp_photo(photo_count)
    video_count = _clamp_video(video_count)
    obstacles_text = ", ".join(obstacles) if obstacles else "없음"
    biz_label = BIZ_TYPE_LABELS.get(biz_type, biz_type)
    process_text = process or solution
    equipment_text = equipment or "미기재"
    media = _media_instructions(photo_count, video_count)
    return f"""현장 팩트만 사용해 아래 4채널 초안을 한 번에 작성하세요.

[업체·현장 팩트]
- 업체 종류: {biz_label}
- 업체 이름: {company_name or "미기재"}
- 주문 내용: {order_detail or "미기재"}
- 작업 위치: {location}
- 고객 인상: {customer_impression or "미기재"}
- 당일 날씨: {weather or "미기재"}
- 해결 사항: {issue}
- 현장 고충/돌발상황: {obstacles_text}
- 해결 과정: {process_text or "미기재"}
- 사용 장비: {equipment_text}
- 고객 반응: {customer_reaction or "미기재"}
- 완료 기분/소감: {feeling or "미기재"}
- 기타 사항: {extra or "없음"}
- 문체 톤: {tone}

[미디어]
{media}

[채널 규칙]
1) naver_blog
   - title: 지역 + 작업 + 결과 1줄
   - content: 방문 계기→작업 순서. 사장님 소감 반영. 미디어 마커 준수
   - tags: "#태그" 형식 8~12개
2) daangn_post: 당근 비즈프로필 소식 4~6줄. 친근한 이모지. 과장·허위 가격 금지.
   "오늘 {location} 다녀왔습니다" 형태로 요약. 사진은 완료 컷 1~2장만 쓰라고 마지막에 한 줄 안내.
3) place_review
   - customer_sms: 포토리뷰 부탁 문자 90~160자. 링크 자리 [플레이스링크]. 대필 금지(부탁만)
   - place_keywords: # 없는 검색 키워드 5~8개
   - place_news: 네이버지도 플레이스 소식 2~4줄. 사진 1장 권장 안내
4) kakao
   - customer_talk: 시공 직후 고객 카톡. 감사+불편 시 연락+후기 부담 없는 부탁. 완료 사진/15초 영상 있으면 같이 보내라는 한 줄
   - channel_post: 카톡 채널/단골용 짧은 현장 소식 2~4줄

반드시 이 JSON만 출력:
{{
  "naver_blog": {{"title": "", "content": "", "tags": []}},
  "daangn_post": "",
  "place_review": {{"customer_sms": "", "place_keywords": [], "place_news": ""}},
  "kakao": {{"customer_talk": "", "channel_post": ""}}
}}
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


def _strip_fences(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        parts = re.split(r"[,|\n]+", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def normalize_channels(payload: Any) -> dict:
    data = payload if isinstance(payload, dict) else {}
    blog = data.get("naver_blog") if isinstance(data.get("naver_blog"), dict) else {}
    place = data.get("place_review") if isinstance(data.get("place_review"), dict) else {}
    kakao = data.get("kakao") if isinstance(data.get("kakao"), dict) else {}
    tags = _as_str_list(blog.get("tags"))
    tags = [t if t.startswith("#") else f"#{t.lstrip('#')}" for t in tags]
    keywords = [k.lstrip("#").strip() for k in _as_str_list(place.get("place_keywords"))]
    daangn = data.get("daangn_post", "")
    if not isinstance(daangn, str):
        daangn = json.dumps(daangn, ensure_ascii=False) if daangn else ""
    return {
        "naver_blog": {
            "title": str(blog.get("title") or "").strip(),
            "content": str(blog.get("content") or "").strip(),
            "tags": tags,
        },
        "daangn_post": daangn.strip(),
        "place_review": {
            "customer_sms": str(place.get("customer_sms") or "").strip(),
            "place_keywords": [k for k in keywords if k],
            "place_news": str(place.get("place_news") or "").strip(),
        },
        "kakao": {
            "customer_talk": str(kakao.get("customer_talk") or "").strip(),
            "channel_post": str(kakao.get("channel_post") or "").strip(),
        },
    }


def channels_to_legacy_result(channels: dict) -> str:
    blog = channels.get("naver_blog") or {}
    tags = " ".join(blog.get("tags") or [])
    title = blog.get("title") or ""
    content = blog.get("content") or ""
    return f"[제목]\n{title}\n[본문]\n{content}\n[태그]\n{tags}".strip()


def parse_channels_json(raw: str) -> dict:
    text = _strip_fences(raw)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse failed: {e}") from e
    out = normalize_channels(parsed)
    if not out["naver_blog"]["title"] and not out["naver_blog"]["content"]:
        raise RuntimeError("JSON missing naver_blog content")
    return out


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
            "responseMimeType": "application/json",
            "temperature": 0.7,
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
                if res.status_code in (429, 503, 504):
                    continue
                continue
            return _extract_text(res.json()), model
        except requests.Timeout:
            last_error = RuntimeError(f"Gemini {model} timeout")
            logger.warning("%s", last_error)
            continue
        except Exception as e:
            last_error = e
            logger.warning("Gemini %s error: %s", model, e)
    raise last_error or RuntimeError("Gemini failed")


def _call_openai(prompt: str) -> str:
    key = _openai_key()
    if not key or key == "your_openai_key":
        raise RuntimeError("OPENAI_API_KEY not configured")

    payload = {
        "model": OPENAI_MODEL,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": JSON_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": _max_tokens(),
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {key}"}
    res = requests.post(
        OPENAI_URL, json=payload, headers=headers, timeout=_openai_timeout()
    )
    if not res.ok:
        raise RuntimeError(f"OpenAI HTTP {res.status_code}: {_http_error_message(res)}")
    return res.json()["choices"][0]["message"]["content"]


def generate_channels(prompt: str) -> tuple[dict, str]:
    last_err = None
    try:
        raw, model = _call_gemini(prompt)
        return parse_channels_json(raw), model
    except Exception as e:
        last_err = e
        if "401" in str(e) or "api_key" in str(e).lower() or "API_KEY_INVALID" in str(e):
            if not _openai_enabled():
                raise
        logger.warning("[Fallback] Gemini failed (%s) -> GPT-4o-mini", e)
        if not _openai_enabled():
            raise

    try:
        raw = _call_openai(prompt)
        return parse_channels_json(raw), OPENAI_MODEL
    except Exception as oe:
        logger.error("OpenAI fallback failed: %s", oe)
        raise RuntimeError(f"Gemini: {last_err} / OpenAI: {oe}") from oe


def generate_content(prompt: str) -> tuple[str, str]:
    """Legacy helper used by older callers."""
    channels, model = generate_channels(prompt)
    return channels_to_legacy_result(channels), model

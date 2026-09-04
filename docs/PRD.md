# Product Requirements Document (PRD) — AutoBlog AI (Zero-Web MVP)

> **문서 버전:** v1.1  
> **최종 수정:** 2026-09-02  
> **상태:** MVP 완료 (Phase 1~5)

---

## 1. Goal & Architecture

### 1.1 목표

별도 웹페이지 없이 **크롬 확장 프로그램 + 경량 백엔드**만으로 현장 블로그 포스팅을 지원한다.

| KPI | 목표 |
|-----|------|
| AI 초안 생성 | **3분 이내** (폼 입력 → 생성 → 검수) |
| 발행까지 (사진 포함) | **10분 이내** |
| 웹사이트 비용 | **0원** (고객용 랜딩·관리자 웹 없음) |
| 결제 연동 | **PG 없음** — 무통장 계좌이체 + 수동 라이선스 발급 |

### 1.2 핵심 제약사항

- 웹사이트 제작/호스팅 **배제** (Chrome Web Store 페이지는 유일한 공개 창구)
- PG사 연동 **배제** — 계좌이체 기반 30일 만료형 라이선스 키
- API 키·라이선스 검증·사용량 한도는 **반드시 백엔드**에서 처리
- 고객용 관리자 웹 **배제** — 운영은 CLI(`manage.py`) + 선택적 Admin API

### 1.3 기술 스택

| 레이어 | 기술 |
|--------|------|
| Client | Chrome Extension **Manifest V3** (Side Panel API) |
| Backend | Python **FastAPI** (로컬 / Render·Railway 무료 티어) |
| 데이터 | **SQLite** (라이선스·일/월 사용량) |
| AI 1순위 | Google **Gemini 2.5 Flash** |
| AI 2순위 | OpenAI **GPT-4o-mini** (Fallback) |
| AI Failover | Gemini **1초 타임아웃** 후 GPT 자동 전환 |

### 1.4 프로젝트 구조

```
blog-chrometool/
├── docs/
│   └── PRD.md
├── backend/
│   ├── main.py              # FastAPI 앱, 라이선스·생성 API
│   ├── database.py          # SQLite 연결·스키마
│   ├── license_service.py   # 검증·한도 체크
│   ├── ai_service.py        # Gemini → GPT 듀얼 엔진
│   ├── manage.py            # 관리자 CLI (키 발급·연장·정지)
│   ├── requirements.txt
│   └── .env.example
└── extension/
    ├── manifest.json
    ├── background.js
    ├── sidepanel.html
    ├── sidepanel.js
    ├── content.js
    └── config.js            # BACKEND_URL 단일 관리
```

---

## 2. Business Model & Operations

### 2.1 서비스 개요

| 항목 | 내용 |
|------|------|
| 서비스명 | 오토블로그 AI (AutoBlog AI) |
| 제품 형태 | 단독 Chrome 확장 프로그램 (Side Panel) |
| 요금 | **월 29,000원** / 30일 라이선스 |
| 결제 | 무통장 계좌이체 → 수동 키 발급 |
| 타깃 | 누수·배관·설비, 입주청소, 에어컨 세척, 간판 등 **지역 기반 1인 현장 자영업자** |

### 2.2 고객 온보딩 (Zero-Web)

1. Chrome Web Store(또는 직접 배포)에서 확장 설치
2. Side Panel 상단에서 **입금 계좌 안내** 확인
3. 입금 후 카톡/문자로 연락 → 운영자가 키 발급
4. Side Panel에 라이선스 키 입력 → 잔여일·사용량 표시 → AI 기능 활성화

### 2.3 운영자 워크플로우

```bash
# 유료 30일 발급
python manage.py create --plan paid --days 30 --note "홍길동 누수업"

# 가족·지인 무료 (1/3/6/12개월)
python manage.py create --plan family_free --months 6 --note "사촌 청소업"

# 연장
python manage.py extend --key XXXX-XXXX-XXXX --days 30

# 한도 상향
python manage.py set-limit --key XXXX-XXXX-XXXX --daily 20

# 정지
python manage.py suspend --key XXXX-XXXX-XXXX
```

**할인(반값 등):** MVP에서는 입금액에 비례한 연장 일수를 운영자가 수동 계산 후 `extend` 처리.

```
연장 일수 = floor(입금액 / 29000 × 30)
예: 15,000원 → 15일 연장
```

---

## 3. License System

### 3.1 키 형식

- **랜덤 키:** `XXXX-XXXX-XXXX` (전화번호를 키로 사용하지 않음)
- 데모 키: `DEMO-KEY` (개발·체험용, 별도 낮은 한도)

### 3.2 라이선스 플랜

| plan | 설명 |
|------|------|
| `paid` | 입금 확인 후 30일 |
| `family_free` | 가족·지인 무료 (1/3/6/12개월) |
| `demo` | 체험용 |
| `suspended` | 정지 |

### 3.3 확장 프로그램 UI 상태

**미인증**
- 상단 배너: 입금 계좌 + 오픈카톡/전화 문의
- `[AI 글 생성]` 버튼 비활성화

**인증 완료**
- 배너: `구독 활성 (D-28일) · 오늘 3/10건`
- AI 생성·에디터 전송 기능 개방

**한도 도달**
- `오늘 생성 한도(10건)를 모두 사용했습니다. 내일 다시 이용 가능합니다.`

### 3.4 로컬 캐싱

- `chrome.storage.local`에 라이선스 키 저장 → 브라우저 재시작 후 재입력 불필요
- 앱 시작 시 백엔드 재검증 필수

---

## 4. Usage Limits (비용 폭증 방지)

> 한도는 **백엔드에서만** 집계·강제. 클라이언트 UI 비활성화는 보조 수단.

| 유형 | 일일 한도 | 월간 한도 |
|------|-----------|-----------|
| 유료 (`paid`) | **10건** | **200건** |
| 가족 무료 (`family_free`) | 10건 | 150건 |
| 데모 (`demo`) | **3건** | 10건 |
| VIP (관리자 개별 설정) | 20건 | 300건 |

**기타 안전장치**
- 1회 생성 `max_tokens`: 2,500 ~ 3,000
- 키당 동시 요청 1건
- 일/월 카운트 리셋: **KST(Asia/Seoul)** 자정 / 월초 기준
- 요청 로그: `license_key, timestamp, model, success`

---

## 5. Core Features

### 5.1 현장 인터뷰 입력 폼

| 필드 | 타입 | 필수 |
|------|------|------|
| 현장 위치 | 단답 | ✅ |
| 오늘의 날씨 | 선택(드롭다운) | — |
| 해결할 문제 | 단답 | ✅ |
| 현장 고충/돌발변수 | 체크박스 (복수) | — |
| 사용 장비/해결 공정 | 단답 | ✅ |
| 사장님 기분/소감 | 단답 | — |
| 글 스타일(톤) | 선택(드롭다운) | ✅ |

**돌발변수 기본 옵션:** 배관 노후, 슬러지 과다, 작업 공간 협소, 타업체 해결 실패

### 5.2 AI 듀얼 엔진

1. Gemini 2.5 Flash 호출 (타임아웃 **1초**)
2. 실패 시 GPT-4o-mini 자동 전환 (사용자 중단 없음)
3. 출력 형식:

```
[제목]
...
[본문]
...
[태그]
...
```

> v1.1에서 API 응답을 `{ title, body, tags }` JSON으로 구조화 검토 (에디터 주입 정확도 향상)

### 5.3 스마트에디터 ONE 연동

**1순위:** 제목·본문 분리 주입 (`content.js` — `content_scripts` manifest 등록 필수)  
**2순위(Fallback):** 원클릭 클립보드 복사 → 에디터에서 Ctrl+V

> 스마트에디터 DOM은 비공식·변경 가능. **클립보드 Fallback을 기본 성공 경로로 가정**하고, 자동 주입은 v1.1 개선 항목.

**타깃 URL:** `*://blog.naver.com/*` (글쓰기 페이지)

---

## 6. API Specification

### 6.1 `POST /api/license/verify`

**Request**
```json
{ "license_key": "XXXX-XXXX-XXXX" }
```

**Response (성공)**
```json
{
  "valid": true,
  "remaining_days": 28,
  "expires": "2026-10-15",
  "daily_used": 3,
  "daily_limit": 10,
  "monthly_used": 45,
  "monthly_limit": 200
}
```

**Response (실패)**
```json
{ "valid": false, "message": "등록되지 않았거나 만료된 라이선스입니다." }
```

### 6.2 `POST /api/generate`

**Request**
```json
{
  "license_key": "XXXX-XXXX-XXXX",
  "location": "서초구 반포동 아파트",
  "weather": "☀️ 맑고 화창함",
  "issue": "싱크대 하부장 누수",
  "obstacles": ["배관 노후 심각"],
  "solution": "내시경 확인 후 주름관 교체",
  "feeling": "사모님이 박카스를 건네주셔서 보람",
  "tone": "친절하고 꼼꼼한 전문가형"
}
```

**Response**
```json
{ "result": "[제목]\n...\n[본문]\n...\n[태그]\n..." }
```

**에러**
- `403` — 라이선스 만료·정지
- `429` — 일/월 한도 초과
- `500` — 모든 AI 엔진 실패

### 6.3 Admin API (선택, Phase 5)

- `POST /admin/licenses` — `X-Admin-Token` 헤더 필수
- CLI(`manage.py`)가 기본; Admin API는 보조

---

## 7. Extension Permissions

```json
{
  "permissions": ["sidePanel", "activeTab", "scripting", "storage", "clipboardWrite"],
  "host_permissions": [
    "*://blog.naver.com/*",
    "http://127.0.0.1:8000/*"
  ],
  "content_scripts": [{
    "matches": ["*://blog.naver.com/*"],
    "js": ["content.js"]
  }]
}
```

프로덕션 배포 시 `config.js`의 `BACKEND_URL` 및 `host_permissions`에 Render/Railway URL 추가.

---

## 8. Out of Scope (MVP)

- 고객용 웹사이트·관리자 웹 대시보드
- PG/자동결제
- 모바일 앱
- 타 블로그 플랫폼 (티스토리, 브런치 등)
- 이미지 자동 업로드
- SEO 분석·키워드 리서치

---

## 9. Development Phases

| Phase | 내용 | 산출물 |
|-------|------|--------|
| **1** | 백엔드 기반 | FastAPI, SQLite, 라이선스 검증 API, `manage.py`, `.env.example` |
| **2** | AI 생성 API | Gemini→GPT 듀얼 엔진, 한도 체크, `/api/generate` |
| **3** | Chrome 확장 UI | manifest, Side Panel, 라이선스 게이팅, 폼, storage |
| **4** | 에디터 연동 | content.js 주입 + 클립보드 Fallback, programmatic inject 보완 |
| **5** | 운영·배포 | Admin API(선택), 프로덕션 URL 설정, OPERATIONS.md |

---

## 10. Risk & Mitigation

| 리스크 | 대응 |
|--------|------|
| 라이선스 키 유출 | 랜덤 키 + 일 10건 상한 + 정지 CLI |
| AI 비용 폭증 | 백엔드 한도 + max_tokens + 사용 로그 |
| 스마트에디터 DOM 변경 | 클립보드 Fallback 기본, 주입은 보조 |
| 무료 티어 콜드스타트 | 첫 요청 지연 안내 (Side Panel) |
| Chrome Web Store 심사 | 권한 최소화, 개인정보 처리방침 문구 |

---

## 11. Changelog (PRD v1.0 → v1.1)

| 항목 | v1.0 (초안) | v1.1 (확정) |
|------|-------------|-------------|
| 시간 KPI | 10분 컷만 명시 | AI 3분 + 발행 10분 분리 |
| 요금 | 미명시 | 월 29,000원 |
| 라이선스 키 | 전화번호 예시 | 랜덤 `XXXX-XXXX-XXXX` |
| 사용량 한도 | 없음 | 일 10 / 월 200 (데모 3/10) |
| 데이터 저장 | 메모리 dict | SQLite |
| 관리자 | LICENSES 수동 편집 | `manage.py` CLI |
| content.js | manifest 미등록 | content_scripts 등록 필수 |
| Failover | 1초 (PRD만) | 1초 타임아웃 구현 확정 |
| 에디터 주입 | 1순위 가정 | 클립보드 Fallback을 현실적 기본 경로로 명시 |

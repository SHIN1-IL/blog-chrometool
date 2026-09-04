# AutoBlog AI — 운영 가이드

> 고객용 웹사이트 없이 **CLI + (선택) Admin API**로 라이선스를 관리합니다.

---

## 1. 일일 운영 흐름

### 1.1 유료 고객 (월 29,000원 / 30일)

1. 고객이 무통장 입금 (국민은행 123-45-678901, 예금주: 신일)
2. 카톡/문자로 입금자명·연락처 확인
3. 라이선스 키 발급 (아래 CLI 또는 Admin API)
4. 고객에게 키 문자/카톡 전달
5. 고객이 Chrome 확장 Side Panel에서 [등록] 클릭

```bash
cd backend
python3 manage.py create --plan paid --days 30 --note "홍길동 누수업"
```

### 1.2 가족·지인 무료

```bash
# 1개월
python3 manage.py create --plan family_free --months 1 --note "사촌 청소업"

# 3 / 6 / 12개월
python3 manage.py create --plan family_free --months 6 --note "아버지 간판업"
```

### 1.3 반값·부분 입금 (할인)

MVP에서는 자동 계산 없이, 입금액에 비례해 연장 일수를 수동 적용합니다.

```
연장 일수 = floor(입금액 ÷ 29,000 × 30)

예) 15,000원 입금 → 15일 연장
python3 manage.py extend --key XXXX-XXXX-XXXX --days 15
```

### 1.4 연장·정지·한도 조정

```bash
# 30일 연장 (키는 그대로, 고객 재입력 불필요)
python3 manage.py extend --key XXXX-XXXX-XXXX --days 30

# 정지 (키 유출·환불 시)
python3 manage.py suspend --key XXXX-XXXX-XXXX

# 재활성화
python3 manage.py activate --key XXXX-XXXX-XXXX

# VIP 한도 상향 (일 20건)
python3 manage.py set-limit --key XXXX-XXXX-XXXX --daily 20 --monthly 300

# 전체 목록
python3 manage.py list

# 상세 조회
python3 manage.py show --key XXXX-XXXX-XXXX
```

---

## 2. 사용량 한도 (기본값)

| 플랜 | 일일 | 월간 |
|------|------|------|
| paid | 10건 | 200건 |
| family_free | 10건 | 150건 |
| demo (DEMO-KEY) | 3건 | 10건 |

한도는 **백엔드에서만** 강제됩니다. 운영자가 `set-limit`으로 개별 조정 가능합니다.

---

## 3. Admin API (선택)

`ADMIN_TOKEN` 환경변수 설정 시 활성화됩니다. 터미널 없이 curl/Postman으로 관리할 때 사용합니다.

```bash
# .env
ADMIN_TOKEN=your_long_random_secret_here
```

### 3.1 라이선스 발급

```bash
curl -X POST https://your-app.onrender.com/admin/licenses \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your_long_random_secret_here" \
  -d '{
    "plan": "paid",
    "days": 30,
    "note": "홍길동 누수업"
  }'
```

### 3.2 연장

```bash
curl -X POST https://your-app.onrender.com/admin/licenses/XXXX-XXXX-XXXX/extend \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your_long_random_secret_here" \
  -d '{"days": 30}'
```

### 3.3 정지 / 활성화

```bash
curl -X POST https://your-app.onrender.com/admin/licenses/XXXX-XXXX-XXXX/suspend \
  -H "X-Admin-Token: your_long_random_secret_here"

curl -X POST https://your-app.onrender.com/admin/licenses/XXXX-XXXX-XXXX/activate \
  -H "X-Admin-Token: your_long_random_secret_here"
```

### 3.4 목록 조회

```bash
curl https://your-app.onrender.com/admin/licenses \
  -H "X-Admin-Token: your_long_random_secret_here"
```

---

## 4. 백엔드 배포 (Render)

### 4.1 사전 준비

- [Google AI Studio](https://aistudio.google.com/)에서 Gemini API 키 발급
- [OpenAI](https://platform.openai.com/)에서 API 키 발급 (Fallback용)
- Render 계정 생성

### 4.2 Render 배포 절차

1. GitHub에 `blog-chrometool` 저장소 푸시
2. Render → **New Web Service** → 저장소 연결
3. 설정:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** 추가:

| 변수 | 값 |
|------|-----|
| `GEMINI_API_KEY` | (실제 키) |
| `OPENAI_API_KEY` | (실제 키) |
| `ADMIN_TOKEN` | (긴 랜덤 문자열) |
| `DATABASE_PATH` | `/var/data/autoblog.db` |

5. **Disk** 추가 (SQLite 영속화 필수):
   - Mount Path: `/var/data`
   - Size: 1GB

6. 배포 완료 후 `https://your-app.onrender.com/health` → `{"status":"ok"}` 확인

### 4.3 무료 티어 주의사항

- **콜드스타트:** 15분 비활성 후 첫 요청이 30~60초 걸릴 수 있음
- 고객에게 "첫 로딩은 잠시 걸릴 수 있습니다" 안내
- 트래픽 증가 시 유료 플랜 전환 검토

### 4.4 Railway (대안)

Root: `backend`, Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`  
동일한 환경변수 설정. Volume 마운트로 SQLite 경로 지정.

---

## 5. Chrome 확장 프로덕션 배포 체크리스트

스토어 제출 또는 고객 직접 배포 전:

```bash
chmod +x scripts/prepare-production.sh
./scripts/prepare-production.sh
```

- [ ] `extension/config.js` → `ENV = "production"`, `BACKEND_URLS.production` 실제 URL
- [ ] `extension/business.js` → 실제 계좌·연락처 (`business.example.js` 참고)
- [ ] `extension/manifest.json` → `host_permissions`에 프로덕션 URL 추가 (`manifest.prod.snippet.json` 참고)
- [ ] `extension/icons/` 생성: `python3 scripts/generate_icons.py`
- [ ] `docs/PRIVACY_POLICY.md` → 운영자·연락처 입력 후 공개 URL 확보
- [ ] `DEMO-KEY`는 프로덕션 DB에서 제거하거나 비활성화
- [ ] 확장 프로그램 새로고침 후 E2E 테스트

상세: `docs/STORE_LISTING.md`

---

## 6. Chrome Web Store 제출 (참고)

- **권한 설명:** 네이버 블로그 에디터 연동, Side Panel UI, 라이선스 검증 API 통신
- **스크린샷:** Side Panel 폼, 라이선스 배너, 생성 결과
- **개인정보 처리방침:** 수집 항목 — 라이선스 키(로컬 저장), 현장 입력 텍스트(AI 생성 API 전송). 별도 서버 DB에 글 내용 장기 보관하지 않음.
- **단일 목적:** 네이버 블로그 현장 후기 작성 보조

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| Side Panel "서버 연결 실패" | 백엔드 미실행 또는 URL 불일치 | `config.js` URL 확인, `/health` 테스트 |
| 첫 요청만 매우 느림 | Render 콜드스타트 | 재시도 또는 유료 플랜 |
| AI 500 오류 | API 키 미설정·만료 | Render 환경변수 확인 |
| 에디터 주입 실패 | 스마트에디터 DOM 변경 | [클립보드 복사] 사용 |
| 429 한도 초과 | 일/월 한도 도달 | 내일까지 대기 또는 `set-limit` |
| DB 초기화됨 | SQLite 경로에 Disk 미마운트 | `DATABASE_PATH` + Render Disk 설정 |

---

## 8. 보안 체크리스트

- [ ] `ADMIN_TOKEN`을 git에 커밋하지 않음
- [ ] `.env`는 `.gitignore`에 포함됨
- [ ] API 키는 Render 환경변수로만 관리
- [ ] 유출 의심 키는 즉시 `suspend`
- [ ] `DEMO-KEY`를 프로덕션에 그대로 두지 않음

---

## 9. 빠른 시작 (로컬 개발)

```bash
# 백엔드
cd backend
cp .env.example .env   # API 키 입력
python3 -m pip install -r requirements.txt
python3 manage.py seed
python3 -m uvicorn main:app --reload

# 확장 프로그램
# Chrome → chrome://extensions → 개발자 모드 → extension/ 폴더 로드
# DEMO-KEY로 등록 후 테스트
```

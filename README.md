# 오토블로그 AI (AutoBlog AI)

네이버 블로그 현장 후기를 **3분**에 작성하는 Chrome 확장 + 모바일 웹 + FastAPI 백엔드.

## 고객 이용 채널

| 기기 | 방법 |
|------|------|
| 핸드폰·태블릿 | https://blog-chrometool.onrender.com/app/ |
| PC 크롬 | `autoblog-extension.zip` 설치 (또는 `extension/` 로드) |

둘 다 같은 라이선스 키·서버를 사용합니다.

## 빠른 시작 (로컬)

```bash
# 1. 백엔드
cd backend
cp .env.example .env          # API 키 입력
pip install -r requirements.txt
python3 manage.py seed
uvicorn main:app --reload

# 2. Chrome 확장
# chrome://extensions → 개발자 모드 → extension/ 폴더 로드
# DEMO-KEY 등록 후 테스트
```

## 프로젝트 구조

```
blog-chrometool/
├── backend/          # FastAPI, SQLite, AI, Admin API
├── extension/        # Chrome MV3 Side Panel
├── docs/
│   ├── PRD.md
│   ├── OPERATIONS.md      # 운영·배포 가이드
│   ├── STORE_LISTING.md   # Chrome Web Store 제출
│   └── PRIVACY_POLICY.md
└── scripts/
    ├── generate_icons.py
    └── prepare-production.sh
```

## 프로덕션 배포

1. Render에 `backend/` 배포 → `docs/OPERATIONS.md` §4
2. `extension/config.js` → `ENV = "production"`, URL 변경
3. `extension/business.js` → 실제 계좌·연락처
4. `./scripts/prepare-production.sh` 실행
5. Chrome Web Store 제출 → `docs/STORE_LISTING.md`

## 문서

| 문서 | 내용 |
|------|------|
| [PRD](docs/PRD.md) | 제품 요구사항 |
| [OPERATIONS](docs/OPERATIONS.md) | 라이선스 발급·Render 배포 |
| [STORE_LISTING](docs/STORE_LISTING.md) | 스토어 등록 |
| [PRIVACY_POLICY](docs/PRIVACY_POLICY.md) | 개인정보 처리방침 |

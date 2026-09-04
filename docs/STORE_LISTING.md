# Chrome Web Store 등록 가이드

## 1. 스토어 등록 정보 (초안)

### 확장 프로그램 이름
```
오토블로그 AI - 사장님 현장 일기
```

### 간단한 설명 (132자 이내)
```
현장 사진만 찍고 3분 체크하면 네이버 블로그 후기 초안이 완성됩니다. 누수·청소·설비 사장님 전용 AI 글쓰기 도우미.
```

### 상세 설명
```
🛠️ 오토블로그 AI — 현장 사장님을 위한 네이버 블로그 후기 작성 도우미

누수, 배관, 입주청소, 에어컨, 간판 등 지역 현장 자영업자를 위해 만들었습니다.
별도 홈페이지 없이 크롬 확장 프로그램만으로 끝납니다.

✅ 이런 분께 추천합니다
· 현장 작업 후 네이버 블로그 마케팅을 하고 싶은 1인 사장님
· 글쓰기가 어렵지만 사진과 현장 이야기는 있는 분
· 지역 키워드 상위노출을 노리는 시공업체

🚀 사용 방법 (3분)
1. Side Panel에서 현장 정보 체크 (위치, 문제, 해결 방법 등)
2. AI가 네이버 블로그 맞춤 초안 생성
3. 사진 첨부 후 네이버 에디터에 붙여넣기 → 발행

💳 구독
· 월 29,000원 / 30일 라이선스
· 무통장 입금 후 키 발급 (확장 프로그램 내 안내)

📌 필요 권한 안내
· blog.naver.com: 스마트에디터 글 주입
· storage: 라이선스 키 로컬 저장
· sidePanel: 작업 패널 UI
```

### 카테고리
`생산성` (Productivity)

### 언어
한국어

---

## 2. 제출 전 체크리스트

```bash
# 프로덕션 준비 검증
chmod +x scripts/prepare-production.sh
./scripts/prepare-production.sh
```

- [ ] `extension/config.js` → `ENV = "production"`, 실제 백엔드 URL
- [ ] `extension/business.js` → 실제 계좌·연락처
- [ ] `extension/manifest.json` → `host_permissions`에 프로덕션 URL
- [ ] `extension/icons/` → 128, 48, 16 PNG (`python3 scripts/generate_icons.py`)
- [ ] Render 백엔드 배포 완료, `/health` 확인
- [ ] `docs/PRIVACY_POLICY.md` → 운영자·연락처 입력
- [ ] 스크린샷 3~5장 (1280x800 또는 640x400 권장)
- [ ] Chrome Web Store 개발자 등록 ($5 일회성)

---

## 3. 스크린샷 촬영 가이드

| # | 화면 | 설명 |
|---|------|------|
| 1 | Side Panel 전체 | 라이선스 + 입력 폼 |
| 2 | AI 생성 결과 | 생성된 제목·본문 미리보기 |
| 3 | 네이버 에디터 | 주입 또는 붙여넣기 완료 화면 |
| 4 | 라이선스 활성 | D-28일 · 사용량 표시 |
| 5 | (선택) 계좌 안내 | 구독 안내 박스 |

---

## 4. 권한 심사 대응 (Justification)

| 권한 | 사유 |
|------|------|
| `sidePanel` | 현장 입력 폼 UI 제공 |
| `storage` | 라이선스 키 로컬 저장 (재입력 방지) |
| `activeTab` / `scripting` | 네이버 블로그 에디터에 글 주입 |
| `clipboardWrite` | 에디터 주입 실패 시 클립보드 복사 |
| `host_permissions: blog.naver.com` | 스마트에디터 ONE 연동 |
| `host_permissions: API URL` | 라이선스 검증 및 AI 생성 API |

---

## 5. 개인정보 처리방침 URL

스토어 제출 시 개인정보 처리방침 URL이 필요합니다.

**옵션 A:** GitHub Pages에 `docs/PRIVACY_POLICY.md` 호스팅  
**옵션 B:** Notion 공개 페이지  
**옵션 C:** Render 정적 페이지 (추후)

`docs/PRIVACY_POLICY.md`의 `[운영자명]`, `[연락처]` 를 실제 정보로 수정 후 공개 URL을 확보하세요.

---

## 6. 패키징 (수동 배포 / 검수용)

```bash
cd extension
zip -r ../autoblog-extension.zip . \
  -x "*.example.js" -x ".DS_Store"
```

Chrome Web Store Developer Dashboard → **New Item** → zip 업로드

---

## 7. 심사 시 주의사항

- 네이버 블로그 DOM 조작은 네이버 이용약관과 충돌할 수 있음 → **클립보드 복사 Fallback**을 기본 경로로 안내
- AI 생성 콘텐츠는 사용자 검수 후 발행하도록 UI에 명시됨
- `DEMO-KEY`는 스토어 버전에서 제거하거나 비활성화 권장

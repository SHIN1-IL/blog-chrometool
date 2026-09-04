#!/bin/bash
# 프로덕션 배포 전 체크리스트 실행
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== AutoBlog AI 프로덕션 준비 체크 ==="
echo ""

ERRORS=0

check_file() {
  if grep -q "$2" "$1" 2>/dev/null; then
    echo "⚠️  $3"
    ERRORS=$((ERRORS + 1))
  else
    echo "✅ $3 (OK)"
  fi
}

# config.js
check_file "extension/config.js" 'ENV = "development"' \
  "extension/config.js → ENV를 production으로 변경"

check_file "extension/config.js" "your-app.onrender.com" \
  "extension/config.js → BACKEND_URLS.production 실제 URL 설정"

# business.js
check_file "extension/business.js" "010-XXXX-XXXX" \
  "extension/business.js → 실제 연락처 설정"

check_file "extension/business.js" "123-45-678901" \
  "extension/business.js → 실제 계좌번호 설정"

# manifest host_permissions
if grep -q "your-app.onrender.com" extension/manifest.json 2>/dev/null; then
  echo "✅ manifest.json 프로덕션 URL (OK)"
elif grep -q "onrender.com" extension/manifest.json 2>/dev/null; then
  echo "✅ manifest.json 프로덕션 URL 설정됨"
else
  echo "⚠️  manifest.json → host_permissions에 프로덕션 백엔드 URL 추가"
  ERRORS=$((ERRORS + 1))
fi

# icons
for size in 16 48 128; do
  if [ -f "extension/icons/icon${size}.png" ]; then
    echo "✅ icon${size}.png 존재"
  else
    echo "⚠️  icon${size}.png 없음 → python3 scripts/generate_icons.py 실행"
    ERRORS=$((ERRORS + 1))
  fi
done

# backend .env
if [ -f "backend/.env" ]; then
  check_file "backend/.env" "your_gemini_key" "backend/.env → GEMINI_API_KEY 설정"
  check_file "backend/.env" "your_openai_key" "backend/.env → OPENAI_API_KEY 설정"
else
  echo "⚠️  backend/.env 없음 → cp backend/.env.example backend/.env 후 키 입력"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "❌ ${ERRORS}개 항목 확인 필요. docs/OPERATIONS.md 참고."
  exit 1
else
  echo "✅ 프로덕션 배포 준비 완료!"
fi

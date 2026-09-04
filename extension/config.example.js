// 프로덕션 배포 시:
// 1. ENV = "production"
// 2. BACKEND_URLS.production 을 실제 URL로 변경
// 3. manifest.json host_permissions에 프로덕션 URL 추가

const ENV = "production";

const BACKEND_URLS = {
  development: "http://127.0.0.1:8000",
  production: "https://your-app.onrender.com",
};

const BACKEND_URL = BACKEND_URLS[ENV] || BACKEND_URLS.production;

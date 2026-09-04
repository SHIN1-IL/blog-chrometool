// 환경: "development" (로컬) | "production" (Render/Railway)
const ENV = "production";

const BACKEND_URLS = {
  development: "http://127.0.0.1:8000",
  production: "https://blog-chrometool.onrender.com",
};

const BACKEND_URL = BACKEND_URLS[ENV] || BACKEND_URLS.development;

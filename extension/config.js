// 환경: "development" (로컬) | "production" (Render/Railway)
const ENV = "development";

const BACKEND_URLS = {
  development: "http://127.0.0.1:8000",
  production: "https://your-app.onrender.com",
};

const BACKEND_URL = BACKEND_URLS[ENV] || BACKEND_URLS.development;

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 백엔드 CORS 기본값(FRONTEND_ORIGIN=http://localhost:3000), docker-compose, .env.example과
    // 포트를 일치시켜 로컬 dev 서버(`npm run dev`)에서도 CORS 오류 없이 바로 연동되도록 고정한다.
    port: 3000,
  },
  preview: {
    // Azure Container Apps 등 배포 환경에서는 빌드 시점에 알 수 없는 동적 FQDN으로 접근하므로
    // Host 헤더 검증을 해제해 `vite preview`가 해당 도메인을 차단하지 않도록 한다.
    host: true,
    allowedHosts: true,
  },
});

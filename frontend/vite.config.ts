import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 백엔드 CORS 기본값(FRONTEND_ORIGIN=http://localhost:3000), docker-compose, .env.example과
    // 포트를 일치시켜 로컬 dev 서버(`npm run dev`)에서도 CORS 오류 없이 바로 연동되도록 고정한다.
    port: 3000,
  },
})

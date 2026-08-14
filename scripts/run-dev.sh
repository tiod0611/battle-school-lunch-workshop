#!/bin/bash
# 급식배틀 앱을 로컬에서 한 번에 실행하는 스크립트 (백엔드 + 프론트엔드).
# 사전 준비: .env.example을 .env로 복사하고 NEIS_API_KEY를 입력해야 합니다.
# 사용법: 프로젝트 루트에서 `bash scripts/run-dev.sh` 실행

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "경고: .env 파일이 없습니다. .env.example을 복사한 뒤 NEIS_API_KEY를 입력하세요." >&2
fi

cleanup() {
  echo "서버를 종료합니다..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$ROOT_DIR/backend" && python3 -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

(cd "$ROOT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "백엔드(:8000)와 프론트엔드(:3000)가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요."
wait

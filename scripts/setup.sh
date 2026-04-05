#!/bin/bash
# GuraNo - Development environment setup
set -e

echo "=== GuraNo 개발환경 셋업 ==="

# Backend
echo "[1/4] Backend 의존성 설치..."
cd backend
python -m venv .venv
source .venv/bin/activate 2>/dev/null || .venv/Scripts/activate 2>/dev/null
pip install -r requirements.txt
cd ..

# Frontend
echo "[2/4] Frontend 의존성 설치..."
cd frontend
npm install
cd ..

# Environment
echo "[3/4] 환경 설정 파일 생성..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env 파일이 생성되었습니다. 필요한 API 키를 설정하세요."
fi

# Directories
echo "[4/4] 필수 디렉토리 생성..."
mkdir -p captures

echo ""
echo "=== 셋업 완료! ==="
echo "실행 방법:"
echo "  방법 1 (Docker):   docker-compose up"
echo "  방법 2 (수동):"
echo "    백엔드: cd backend && uvicorn app.main:app --reload"
echo "    프론트: cd frontend && npm run dev"
echo ""
echo "접속: http://localhost:5173"

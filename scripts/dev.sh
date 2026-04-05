#!/bin/bash
# Run backend + frontend simultaneously for development
set -e

echo "=== GuraNo 개발 서버 시작 ==="

# Start backend
cd backend
echo "Backend 시작 (port 8000)..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
echo "Frontend 시작 (port 5173)..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "접속: http://localhost:5173"
echo "종료: Ctrl+C"

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

# GuraNo - AI 거짓말 탐지기

음성, 얼굴 표정, 심박수를 종합 분석하여 실시간으로 거짓말을 탐지하는 AI 시스템

## 기능
- **3채��� 분석**: 음성(피치, 쉼, 떨림) + 얼굴(미세표정, 가짜 미소, AU) + 심박수(HR, HRV)
- **Late Fusion**: 3채널 종합 판정 (Logistic Regression)
- **AI 자동 질문**: 미리 입력한 질문을 TTS로 자동 읽어줌
- **실시간 판정**: 거짓 감지 시 스크린샷 + 이유 자동 생성
- **PC + 모바일**: 웹 브라우저 기반, 반응형 UI
- **심박수 3채널**: Apple Watch / BLE 밴드 / 웹캠 rPPG

## 실행

### Docker (권장)
```bash
docker-compose up
```

### 수동 실행
```bash
# 백엔드
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 프론트엔드
cd frontend
npm install
npm run dev
```

접속: http://localhost:5173

## 기술 스택
- **백엔드**: Python, FastAPI, WebSocket, SQLAlchemy
- **분석**: MediaPipe, Whisper STT, XGBoost
- **프론트**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **심박**: Apple Watch (HealthKit), Web Bluetooth, rPPG

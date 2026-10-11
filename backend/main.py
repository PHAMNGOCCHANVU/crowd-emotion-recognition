import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Đảm bảo đường dẫn import cho toàn bộ backend
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
load_dotenv(ROOT_DIR / ".env", override=False)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import engine, Base
from backend.api.sessions import router as sessions_router
from backend.api.questions import router as questions_router

# Tự động tạo bảng SQLite nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Mock Interview Platform API",
    description="Backend API cho Nền tảng Phỏng vấn thử Đa phương thức (FER + Groq Whisper + Gemini)",
    version="1.0.0",
)

# Cho phép kết nối CORS từ Frontend React (Vite dev server cổng 5173 và các cổng thông dụng)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(questions_router)


@app.get("/")
def root():
    return {
        "project": "AI Mock Interview Platform",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

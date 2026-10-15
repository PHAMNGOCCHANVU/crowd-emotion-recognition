import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đảm bảo đường dẫn import cho toàn bộ backend
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

# Ưu tiên nạp backend/.env, sau đó fallback root .env
if (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env", override=False)
elif (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env", override=False)

for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


from backend.database import engine, Base
import backend.models  # Đảm bảo nạp đầy đủ ORM models trước khi tạo bảng
from backend.api.sessions import router as sessions_router
from backend.api.questions import router as questions_router
from backend.api.chatbot import router as chatbot_router

# Tự động ánh xạ và tạo bảng nếu chưa có
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
app.include_router(chatbot_router)



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

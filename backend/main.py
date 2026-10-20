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
from backend.api.segments import router as segments_router
from backend.api.attempts import router as attempts_router
from backend.api.admin import router as admin_router
from backend.api.users import router as users_router
from backend.api.agents import router as agents_router

# Tự động ánh xạ và tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)


def add_missing_columns():
    """create_all không sửa bảng đã tồn tại: tự thêm các cột còn thiếu (DB cũ trên Render/PostgreSQL)."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        present = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in present:
                continue
            col_type = col.type.compile(dialect=engine.dialect)
            try:
                with engine.begin() as conn:
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}'))
                print(f"Added missing column {table.name}.{col.name}")
            except Exception as exc:
                print(f"Could not add column {table.name}.{col.name}: {exc}")


add_missing_columns()

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
app.include_router(segments_router)
app.include_router(attempts_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(agents_router)


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

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Tự động nạp cấu hình từ file .env (ưu tiên backend/.env sau đó root .env)
if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
elif (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env")

# Cấu hình Database URL (Hỗ trợ PostgreSQL qua biến môi trường, mặc định SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_PATH = BASE_DIR / "interview.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Chuẩn hóa tiền tố postgres:// thành postgresql:// (cho Render, Railway, Supabase)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

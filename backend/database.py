import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cấu hình Database URL (Hỗ trợ PostgreSQL qua biến môi trường, mặc định SQLite)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    BASE_DIR = Path(__file__).resolve().parent
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

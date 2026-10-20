"""
Common test fixtures and utilities for API integration & security tests.
Provides in-memory SQLite isolation, seeded sample data, and configured TestClient.
"""

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
import backend.models as models
from backend.security import get_password_hash


@pytest.fixture
def db_session():
    """Create a completely isolated in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed core test users
    admin_user = models.User(
        id="admin_123",
        email="admin@mockinterview.ai",
        full_name="Quản Trị Viên Hệ Thống",
        role="ADMIN",
        phone_number="0901234567",
        hashed_password=get_password_hash("Admin@123456"),
    )
    candidate_user = models.User(
        id="user_123",
        email="candidate@mockinterview.ai",
        full_name="Nguyễn Văn Ứng Viên",
        role="USER",
        phone_number="0912345678",
        hashed_password=get_password_hash("User@123456"),
    )
    session.add_all([admin_user, candidate_user])

    # Seed sample industry and position
    it_industry = models.Industry(
        id="it_software",
        code="IT_SW",
        name="Công nghệ phần mềm",
        status="ACTIVE",
    )
    session.add(it_industry)

    backend_pos = models.Position(
        id="backend_dev",
        industry_id="it_software",
        name="Backend Developer",
        code="BE_DEV",
        skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
        duration="3–6 tháng",
        icon="server",
        status="ACTIVE",
    )
    session.add(backend_pos)

    # Seed sample questions
    q1 = models.Question(
        id="q_be_01",
        position_id="backend_dev",
        question_text="Em hãy giải thích nguyên lý ACID trong CSDL quan hệ?",
        correct_answer="A",
        level="junior",
        levels=["junior", "mid"],
        category="Chuyên môn",
        time_limit_seconds=120,
    )
    q2 = models.Question(
        id="q_be_02",
        position_id="backend_dev",
        question_text="Khi nào nên dùng async def và def thông thường trong FastAPI?",
        correct_answer="A",
        level="mid",
        levels=["mid", "senior"],
        category="Chuyên môn",
        time_limit_seconds=120,
    )
    session.add_all([q1, q2])

    # Seed sample test and attempt
    sample_test = models.Test(
        id="test_be_01",
        title="Bài kiểm tra Backend Cơ bản",
        description="Kiểm tra kiến thức Backend",
    )
    session.add(sample_test)

    sample_attempt = models.Attempt(
        id="att_01",
        user_id="user_123",
        test_id="test_be_01",
        total_score=0.0,
        max_score=20.0,
        status="IN_PROGRESS",
        started_at=datetime.utcnow(),
    )
    session.add(sample_attempt)

    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

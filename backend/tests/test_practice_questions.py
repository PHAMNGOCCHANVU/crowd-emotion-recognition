"""
Test Suite: Practice Questions & AI Generation from JD (/api/questions & /api/questions/generate-from-jd)
Verification for SPEC-FE-USER-2026-10-21:
- DB migration: columns 'source' and 'created_at' in 'questions' table
- Filtering: GET /api/questions?source=DEFAULT, GET /api/questions?source=Q-JD, level, position
- Generation: POST /api/questions/generate-from-jd (happy path, validation, error handling)
- Security & Regression
"""

from datetime import datetime
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.tests.fixtures_api import db_session, client
import backend.models as models


class TestQuestionsDatabaseMigration:
    """Kiểm tra cấu trúc DB và logic tự động migration cho bảng questions."""

    def test_questions_schema_has_source_and_created_at_columns(self, db_session):
        """Xác minh bảng questions có đủ 2 cột mới: source và created_at."""
        inspector = inspect(db_session.bind)
        columns = {c["name"]: c for c in inspector.get_columns("questions")}

        assert "source" in columns, "Cột 'source' phải tồn tại trong bảng questions"
        assert "created_at" in columns, "Cột 'created_at' phải tồn tại trong bảng questions"

        # Kiểm tra kiểu và thuộc tính cơ bản
        source_col = columns["source"]
        assert "VARCHAR" in str(source_col["type"]).upper() or "TEXT" in str(source_col["type"]).upper()

    def test_questions_default_source_value(self, db_session):
        """Xác minh các câu hỏi mới tạo mặc định nhận source='DEFAULT'."""
        new_q = models.Question(
            id="q_test_default_source",
            position_id="backend_dev",
            question_text="Kiểm tra giá trị mặc định của source",
            level="junior",
        )
        db_session.add(new_q)
        db_session.commit()

        fetched = db_session.query(models.Question).filter(models.Question.id == "q_test_default_source").first()
        assert fetched is not None
        assert fetched.source == "DEFAULT"
        assert fetched.created_at is not None

    def test_migration_routine_on_legacy_table(self):
        """Mô phỏng nâng cấp tự động cho bảng questions từ cấu trúc DB cũ (thiếu source & created_at)."""
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

        # Tạo bảng questions phiên bản cũ (thiếu cột source và created_at)
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE questions (
                    id VARCHAR(50) PRIMARY KEY,
                    position_id VARCHAR(36),
                    category VARCHAR(50),
                    question_text TEXT NOT NULL,
                    correct_answer TEXT,
                    time_limit_seconds INTEGER,
                    level VARCHAR(50)
                );
            """))
            conn.execute(text("""
                INSERT INTO questions (id, position_id, question_text, level)
                VALUES ('legacy_q1', 'backend_dev', 'Câu hỏi từ hệ thống cũ', 'junior');
            """))
            conn.commit()

            # Chạy logic migration giống như trong backend/init_db.py
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            if "questions" in table_names:
                cols = [c["name"] for c in inspector.get_columns("questions")]
                if "source" not in cols:
                    conn.execute(text("ALTER TABLE questions ADD COLUMN source VARCHAR(20) DEFAULT 'DEFAULT';"))
                    conn.commit()
                if "created_at" not in cols:
                    conn.execute(text("ALTER TABLE questions ADD COLUMN created_at DATETIME;"))
                    conn.commit()
                conn.execute(text("UPDATE questions SET source = 'DEFAULT' WHERE source IS NULL;"))
                conn.commit()

            # Xác minh sau migration
            inspector_after = inspect(engine)
            cols_after = [c["name"] for c in inspector_after.get_columns("questions")]
            assert "source" in cols_after
            assert "created_at" in cols_after

            # Kiểm tra dữ liệu cũ đã được gán 'DEFAULT'
            result = conn.execute(text("SELECT id, source FROM questions WHERE id = 'legacy_q1'")).first()
            assert result[0] == "legacy_q1"
            assert result[1] == "DEFAULT"


class TestPracticeQuestionsAPI:
    """Kiểm thử API GET /api/questions phục vụ phân hệ Ôn luyện."""

    def test_get_questions_filter_default_source(self, client, db_session):
        """Happy Path: Lọc câu hỏi nguồn DEFAULT."""
        # Thêm câu hỏi Q-JD để đối chiếu
        q_jd = models.Question(
            id="q_jd_sample_1",
            position_id="backend_dev",
            question_text="Câu hỏi từ JD về FastAPI và SQL",
            source="Q-JD",
            level="junior",
            levels=["junior"],
        )
        db_session.add(q_jd)
        db_session.commit()

        response = client.get("/api/questions?position_id=backend_dev&source=DEFAULT")
        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == "backend_dev"
        assert data["total"] >= 1
        for q in data["questions"]:
            assert q["source"] == "DEFAULT"
        assert all(q["id"] != "q_jd_sample_1" for q in data["questions"])

    def test_get_questions_filter_q_jd_source(self, client, db_session):
        """Happy Path: Lọc câu hỏi nguồn Q-JD."""
        q_jd = models.Question(
            id="q_jd_sample_2",
            position_id="backend_dev",
            question_text="Câu hỏi sinh từ JD về tối ưu async",
            source="Q-JD",
            level="mid",
            levels=["mid"],
            created_at=datetime.utcnow(),
        )
        db_session.add(q_jd)
        db_session.commit()

        response = client.get("/api/questions?position_id=backend_dev&source=Q-JD")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for q in data["questions"]:
            assert q["source"] == "Q-JD"
        assert any(q["id"] == "q_jd_sample_2" for q in data["questions"])

    def test_get_questions_filter_source_all(self, client, db_session):
        """Happy Path: Lọc với source=all lấy cả 2 loại nguồn DEFAULT và Q-JD."""
        q_jd = models.Question(
            id="q_jd_sample_all",
            position_id="backend_dev",
            question_text="Câu hỏi JD trong danh sách all",
            source="Q-JD",
            level="junior",
            levels=["junior"],
        )
        db_session.add(q_jd)
        db_session.commit()

        response = client.get("/api/questions?position_id=backend_dev&source=all")
        assert response.status_code == 200
        data = response.json()
        sources = {q["source"] for q in data["questions"]}
        assert "DEFAULT" in sources
        assert "Q-JD" in sources

    def test_get_questions_filter_position_and_level_and_source(self, client, db_session):
        """Happy Path: Kết hợp lọc position_id + level + source."""
        response = client.get("/api/questions?position_id=backend_dev&level=junior&source=DEFAULT")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "junior"
        for q in data["questions"]:
            assert q["source"] == "DEFAULT"
            assert q["level"] == "junior"

    def test_get_questions_filter_source_not_found(self, client):
        """Edge Case: Lọc theo source không tồn tại trả về danh sách rỗng."""
        response = client.get("/api/questions?position_id=backend_dev&source=UNKNOWN_SOURCE")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["questions"] == []


class TestGenerateQuestionsFromJDAPI:
    """Kiểm thử API POST /api/questions/generate-from-jd."""

    def test_generate_from_jd_happy_path(self, client, db_session):
        """Happy Path: Sinh câu hỏi thành công từ JD hợp lệ, lưu vào DB với source='Q-JD'."""
        valid_payload = {
            "position_id": "backend_dev",
            "level": "junior",
            "jd_text": "Tuyển dụng Backend Developer có kinh nghiệm thực tế về Python, FastAPI, PostgreSQL và tối ưu truy vấn cơ sở dữ liệu.",
        }

        response = client.post("/api/questions/generate-from-jd", json=valid_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["generated_count"] >= 1
        assert len(data["questions"]) >= 1

        for item in data["questions"]:
            assert item["id"].startswith("qjd_")
            assert item["source"] == "Q-JD"
            assert item["level"] == "junior"
            assert len(item["question_text"]) > 10
            assert item["created_at"] is not None

        # Xác minh câu hỏi đã được lưu bền vững vào DB
        saved_qs = db_session.query(models.Question).filter(
            models.Question.position_id == "backend_dev",
            models.Question.source == "Q-JD",
        ).all()
        assert len(saved_qs) >= data["generated_count"]

    def test_generate_from_jd_too_short_text(self, client):
        """Failure Mode: JD ngắn dưới 20 ký tự trả về 400 hoặc 422 Unprocessable Entity."""
        payload = {
            "position_id": "backend_dev",
            "level": "junior",
            "jd_text": "Ngắn quá < 20",
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code in [400, 422]

    def test_generate_from_jd_empty_or_whitespace_text(self, client):
        """Failure Mode: JD toàn khoảng trắng (>20 ký tự khoảng trắng) vi phạm logic strip() trả về 400 Bad Request."""
        payload = {
            "position_id": "backend_dev",
            "level": "junior",
            "jd_text": "                          ",  # 26 ký tự khoảng trắng
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code == 400
        assert "tối thiểu 20 ký tự" in response.json()["detail"]

    def test_generate_from_jd_empty_string(self, client):
        """Validation: JD là chuỗi rỗng trả về 400 hoặc 422."""
        payload = {
            "position_id": "backend_dev",
            "level": "junior",
            "jd_text": "",
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code in [400, 422]

    def test_generate_from_jd_role_not_found(self, client):
        """Failure Mode: position_id không tồn tại trong DB trả về 404 Not Found."""
        payload = {
            "position_id": "unknown_position_id_xyz",
            "level": "junior",
            "jd_text": "Tuyển dụng vị trí lập trình viên với yêu cầu chi tiết đầy đủ hơn 20 ký tự.",
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code == 404
        assert "Không tìm thấy vị trí tuyển dụng" in response.json()["detail"]

    def test_generate_from_jd_invalid_level(self, client):
        """Failure Mode: Level không thuộc danh mục hợp lệ trả về 400 Bad Request."""
        payload = {
            "position_id": "backend_dev",
            "level": "expert_master_supreme",
            "jd_text": "Tuyển dụng Backend Developer có kinh nghiệm thực tế về Python và FastAPI.",
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code == 400
        assert "Level không hợp lệ" in response.json()["detail"]

    def test_generate_from_jd_missing_required_fields(self, client):
        """Validation: Thiếu trường bắt buộc trả về 422 Unprocessable Entity."""
        # Thiếu jd_text
        response = client.post(
            "/api/questions/generate-from-jd",
            json={"position_id": "backend_dev", "level": "junior"},
        )
        assert response.status_code == 422

        # Thiếu position_id
        response = client.post(
            "/api/questions/generate-from-jd",
            json={"level": "junior", "jd_text": "Tuyển dụng Backend Developer hơn 20 ký tự."},
        )
        assert response.status_code == 422

    def test_generate_from_jd_sql_injection_in_jd(self, client):
        """Security: Input JD chứa SQL Injection hoặc thẻ HTML/Script được xử lý an toàn."""
        payload = {
            "position_id": "backend_dev",
            "level": "junior",
            "jd_text": "DROP TABLE questions; SELECT * FROM users; <script>alert('xss')</script> Backend Developer Python FastAPI.",
        }
        response = client.post("/api/questions/generate-from-jd", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert len(data["questions"]) >= 1

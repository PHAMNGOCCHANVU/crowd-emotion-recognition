"""
Test Suite: Sessions API (/api/sessions/history, /api/sessions/recent, /api/sessions/start)
Covers Happy Path, Boundary/Edge Cases, Failure Modes, and Security.
"""

from datetime import datetime
import pytest
from backend.tests.fixtures_api import db_session, client
import backend.models as models


def seed_completed_session(db_session, user_id="user_123", session_id="sess_01"):
    """Helper tạo phiên phỏng vấn hoàn thành có điểm số chi tiết."""
    sess = models.InterviewSession(
        id=session_id,
        user_id=user_id,
        role_name="Software Engineer",
        level="junior",
        status="COMPLETED",
        overall_score=85.5,
        created_at=datetime.utcnow(),
    )
    db_session.add(sess)

    d1 = models.SessionDetail(
        id=f"{session_id}_d1",
        session_id=session_id,
        order_index=1,
        question_text="Bạn hãy giới thiệu bản thân?",
        status="COMPLETED",
        content_score=85.0,
        confidence_score=80.0,
        stress_score=20.0,
        filler_words_count=2,
        ai_feedback={"general_feedback": "Trả lời rõ ràng, lưu loát."},
    )
    d2 = models.SessionDetail(
        id=f"{session_id}_d2",
        session_id=session_id,
        order_index=2,
        question_text="Kinh nghiệm giải quyết xung đột?",
        status="COMPLETED",
        content_score=86.0,
        confidence_score=78.0,
        stress_score=22.0,
        filler_words_count=1,
        ai_feedback={"general_feedback": "Bám sát mô hình STAR tốt."},
    )
    db_session.add_all([d1, d2])
    db_session.commit()
    return sess


class TestSessionHistoryAPI:
    """Kiểm thử lịch sử phỏng vấn (/api/sessions/history)."""

    def test_session_history_happy_path(self, client, db_session):
        """Happy Path: Lấy toàn bộ lịch sử các phiên hoàn thành."""
        seed_completed_session(db_session, user_id="user_123", session_id="sess_h1")
        response = client.get("/api/sessions/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        item = data[0]
        assert item["role_name"] == "Software Engineer"
        assert item["level"] == "junior"
        assert item["overall_score"] == 85.5
        assert item["content_score"] == 85.5
        assert item["filler_count"] == 3  # 2 + 1
        assert "feedback" in item

    def test_session_history_filter_user_id(self, client, db_session):
        """Happy Path: Lọc lịch sử theo đúng user_id."""
        seed_completed_session(db_session, user_id="user_123", session_id="sess_u1")
        seed_completed_session(db_session, user_id="other_user", session_id="sess_u2")

        res_u1 = client.get("/api/sessions/history?user_id=user_123")
        assert res_u1.status_code == 200
        assert all(s["session_id"] == "sess_u1" for s in res_u1.json())

    def test_session_history_nonexistent_user(self, client):
        """Edge Case: Truy vấn user không tồn tại trả về danh sách rỗng."""
        response = client.get("/api/sessions/history?user_id=ghost_user_999")
        assert response.status_code == 200
        assert response.json() == []

    def test_session_history_sql_injection(self, client):
        """Security: Input user_id chứa SQL Injection không gây lỗi 500."""
        response = client.get("/api/sessions/history?user_id=' OR '1'='1")
        assert response.status_code == 200
        assert response.json() == []


class TestRecentSessionsAPI:
    """Kiểm thử phiên gần nhất (/api/sessions/recent)."""

    def test_recent_sessions_happy_path(self, client, db_session):
        """Happy Path: Lấy tối đa limit phiên gần nhất."""
        seed_completed_session(db_session, user_id="user_123", session_id="sess_r1")
        seed_completed_session(db_session, user_id="user_123", session_id="sess_r2")
        seed_completed_session(db_session, user_id="user_123", session_id="sess_r3")

        response = client.get("/api/sessions/recent?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_recent_sessions_boundary_limit_zero(self, client):
        """Boundary/Failure Mode: limit = 0 vi phạm ge=1 trả về 422."""
        response = client.get("/api/sessions/recent?limit=0")
        assert response.status_code == 422

    def test_recent_sessions_boundary_limit_negative(self, client):
        """Boundary/Failure Mode: limit âm vi phạm ge=1 trả về 422."""
        response = client.get("/api/sessions/recent?limit=-5")
        assert response.status_code == 422

    def test_recent_sessions_boundary_limit_excessive(self, client):
        """Boundary/Failure Mode: limit > 20 vi phạm le=20 trả về 422."""
        response = client.get("/api/sessions/recent?limit=25")
        assert response.status_code == 422


class TestSessionStartAPI:
    """Kiểm thử khởi tạo phỏng vấn (/api/sessions/start)."""

    def test_session_start_default_role(self, client):
        """Happy Path: Bắt đầu phỏng vấn vị trí mặc định."""
        payload = {
            "role_name": "Software Engineer",
            "level": "junior",
            "user_id": "user_123",
        }
        response = client.post("/api/sessions/start", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert len(data["questions"]) == 3
        assert data["questions"][0]["order_index"] == 1

    def test_session_start_with_specific_question_ids(self, client):
        """Happy Path: Bắt đầu phỏng vấn với question_ids được chọn cụ thể."""
        payload = {
            "role_name": "Backend Developer",
            "level": "junior",
            "user_id": "user_123",
            "question_ids": ["q_be_01"],
        }
        response = client.post("/api/sessions/start", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["questions"]) == 1
        assert "ACID" in data["questions"][0]["question_text"]

    def test_session_start_nonexistent_question_ids_fallback(self, client):
        """Edge Case: question_ids không có trong DB thì tự động fallback sinh câu hỏi."""
        payload = {
            "role_name": "Software Engineer",
            "level": "mid",
            "question_ids": ["non_existent_q1", "non_existent_q2"],
        }
        response = client.post("/api/sessions/start", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert len(data["questions"]) == 3

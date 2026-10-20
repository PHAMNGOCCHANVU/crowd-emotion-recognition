"""
Test Suite: User Attempts API (/api/user/attempts)
Covers Happy Path, Scoring Calculation, Attempt Lifecycle, IDOR Protection, Failure Modes, and Boundary Cases.
"""

from datetime import datetime
import pytest
from backend.tests.fixtures_api import db_session, client
import backend.models as models


class TestUserAttemptsAPI:
    """Kiểm thử lịch sử làm bài và chấm điểm (/api/user/attempts)."""

    def test_get_user_attempts_happy_path(self, client):
        """Happy Path: Lấy danh sách lượt làm bài của ứng viên."""
        response = client.get("/api/user/attempts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        att = data[0]
        assert att["id"] == "att_01"
        assert att["status"] == "IN_PROGRESS"

    def test_submit_answer_correct(self, client):
        """Happy Path: Nộp đáp án đúng ('A') nhận đủ 10.0 điểm."""
        payload = {
            "question_id": "q_be_01",
            "user_answer": "A",
        }
        response = client.post("/api/user/attempts/att_01/submit-answer", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert "Đã lưu câu trả lời" in data["message"]

    def test_submit_answer_wrong(self, client):
        """Happy Path: Nộp đáp án sai ('B') nhận 0.0 điểm."""
        payload = {
            "question_id": "q_be_02",
            "user_answer": "B",
        }
        response = client.post("/api/user/attempts/att_01/submit-answer", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False

    def test_submit_answer_case_insensitive_and_whitespace(self, client):
        """Boundary Case: Đáp án có khoảng trắng và chữ thường ' a ' vẫn khớp đúng."""
        payload = {
            "question_id": "q_be_01",
            "user_answer": "  a  ",
        }
        response = client.post("/api/user/attempts/att_01/submit-answer", json=payload)
        assert response.status_code == 200
        assert response.json()["is_correct"] is True

    def test_submit_answer_nonexistent_attempt(self, client):
        """Failure Mode: Nộp câu trả lời cho attempt không tồn tại trả về 400."""
        payload = {"question_id": "q_be_01", "user_answer": "A"}
        response = client.post("/api/user/attempts/ghost_att_999/submit-answer", json=payload)
        assert response.status_code == 400
        assert "không tồn tại" in response.json()["detail"]

    def test_complete_attempt_and_total_score_calculation(self, client, db_session):
        """Happy Path: Nộp bài, chốt điểm tổng và chuyển trạng thái COMPLETED."""
        # Nộp 1 câu đúng (10đ) và 1 câu sai (0đ)
        client.post("/api/user/attempts/att_01/submit-answer", json={"question_id": "q_be_01", "user_answer": "A"})
        client.post("/api/user/attempts/att_01/submit-answer", json={"question_id": "q_be_02", "user_answer": "C"})

        # Chốt bài
        comp_res = client.post("/api/user/attempts/att_01/complete")
        assert comp_res.status_code == 200
        assert comp_res.json()["total_score"] == 10.0
        assert "Đã nộp bài" in comp_res.json()["message"]

        # Kiểm tra trạng thái trong DB
        att = db_session.query(models.Attempt).filter(models.Attempt.id == "att_01").first()
        assert att.status == "COMPLETED"
        assert att.total_score == 10.0
        assert att.max_score == 20.0
        assert att.completed_at is not None

    def test_submit_answer_to_completed_attempt_rejected(self, client):
        """Failure Mode: Nộp câu trả lời cho bài thi đã chốt kết quả bị từ chối 400."""
        # Chốt bài trước
        client.post("/api/user/attempts/att_01/complete")

        # Cố nộp thêm câu trả lời
        res = client.post("/api/user/attempts/att_01/submit-answer", json={"question_id": "q_be_01", "user_answer": "A"})
        assert res.status_code == 400
        assert "đã chốt kết quả" in res.json()["detail"]

    def test_complete_already_completed_attempt_rejected(self, client):
        """Failure Mode: Chốt kết quả lần 2 bị từ chối 400."""
        client.post("/api/user/attempts/att_01/complete")
        res2 = client.post("/api/user/attempts/att_01/complete")
        assert res2.status_code == 400
        assert "Không thể chốt bài" in res2.json()["detail"]

    def test_get_attempt_detail_happy_path(self, client):
        """Happy Path: Lấy thông tin chi tiết bài thi."""
        client.post("/api/user/attempts/att_01/submit-answer", json={"question_id": "q_be_01", "user_answer": "A"})
        response = client.get("/api/user/attempts/att_01")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "att_01"
        assert len(data["answers"]) == 1
        assert data["answers"][0]["is_correct"] is True

    def test_get_attempt_detail_not_found(self, client):
        """Failure Mode: Xem chi tiết attempt không tồn tại trả về 404."""
        response = client.get("/api/user/attempts/non_existent_att")
        assert response.status_code == 404

    def test_get_attempt_detail_idor_forbidden(self, client, db_session):
        """Security (IDOR): Xem bài thi thuộc về người dùng khác bị chặn 403 Forbidden."""
        other_attempt = models.Attempt(
            id="att_other_user",
            user_id="victim_user_999",
            test_id="test_be_01",
            total_score=15.0,
            max_score=20.0,
            status="COMPLETED",
        )
        db_session.add(other_attempt)
        db_session.commit()

        # user_123 cố truy cập bài thi của victim_user_999
        response = client.get("/api/user/attempts/att_other_user")
        assert response.status_code == 403
        assert "không có quyền" in response.json()["detail"]

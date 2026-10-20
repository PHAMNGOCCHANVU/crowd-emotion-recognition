"""
Test Suite: Questions & Positions API (/api/questions/positions & /api/questions)
Covers Happy Path, Boundary/Edge Cases, Failure Modes, and Security.
"""

import pytest
from backend.tests.fixtures_api import db_session, client


class TestPositionsAPI:
    """Kiểm thử API danh sách vị trí (/api/questions/positions)."""

    def test_list_positions_happy_path(self, client):
        """Happy Path: Lấy toàn bộ vị trí đang ACTIVE."""
        response = client.get("/api/questions/positions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        pos = data[0]
        assert "id" in pos
        assert "title" in pos
        assert "field" in pos
        assert "skills" in pos
        assert "levels" in pos
        assert pos["id"] == "backend_dev"
        assert "junior" in pos["levels"]

    def test_list_positions_filter_level_matched(self, client):
        """Happy Path: Lọc theo level 'junior' có kết quả khớp."""
        response = client.get("/api/questions/positions?level=junior")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["id"] == "backend_dev" for p in data)

    def test_list_positions_filter_level_unmatched(self, client):
        """Boundary/Edge Case: Lọc theo level không khớp trả về danh sách rỗng."""
        response = client.get("/api/questions/positions?level=nonexistent_level")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_positions_empty_string_level(self, client):
        """Boundary Case: Chuỗi level rỗng không gây lỗi."""
        response = client.get("/api/questions/positions?level=")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_positions_sql_injection_level(self, client):
        """Security: Input level chứa payload SQL Injection không gây lỗi 500."""
        response = client.get("/api/questions/positions?level=' OR '1'='1")
        assert response.status_code == 200
        assert response.json() == []


class TestQuestionsAPI:
    """Kiểm thử API ngân hàng câu hỏi (/api/questions)."""

    def test_list_questions_happy_path(self, client):
        """Happy Path: Lấy danh sách câu hỏi theo position_id."""
        response = client.get("/api/questions?position_id=backend_dev")
        assert response.status_code == 200
        data = response.json()
        assert data["position_id"] == "backend_dev"
        assert data["total"] == 2
        assert len(data["questions"]) == 2

    def test_list_questions_filter_level_junior(self, client):
        """Happy Path: Lọc câu hỏi theo cả position_id và level."""
        response = client.get("/api/questions?position_id=backend_dev&level=junior")
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "junior"
        assert data["total"] == 1
        assert data["questions"][0]["id"] == "q_be_01"

    def test_list_questions_missing_position_id(self, client):
        """Failure Mode: Thiếu query param bắt buộc position_id trả về 422."""
        response = client.get("/api/questions")
        assert response.status_code == 422

    def test_list_questions_nonexistent_position_id(self, client):
        """Edge Case: position_id không tồn tại trong hệ thống trả về total = 0."""
        response = client.get("/api/questions?position_id=unknown_xyz")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["questions"] == []

    def test_list_questions_sql_injection_position_id(self, client):
        """Security: Payload SQL Injection trong position_id không rò rỉ dữ liệu."""
        response = client.get("/api/questions?position_id=' UNION SELECT * FROM users --")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_roles_backward_compatibility(self, client):
        """Happy Path: Endpoint tương thích ngược /api/questions/roles."""
        response = client.get("/api/questions/roles")
        assert response.status_code == 200
        roles = response.json()
        assert isinstance(roles, list)
        assert "Software Engineer" in roles

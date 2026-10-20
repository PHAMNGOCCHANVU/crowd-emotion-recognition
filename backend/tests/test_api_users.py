"""
Test Suite: User Profile & Password API (/api/user/profile & /api/user/change-password)
Covers Happy Path, Password Verification, Validation Rules, Failure Modes, and Security.
"""

import pytest
from backend.tests.fixtures_api import db_session, client
from backend.security import verify_password
import backend.models as models


USER_HEADERS = {"X-User-Id": "user_123"}


class TestUserProfileAPI:
    """Kiểm thử thông tin người dùng (/api/user/profile)."""

    def test_get_profile_happy_path(self, client):
        """Happy Path: Lấy thông tin cá nhân của người dùng hiện tại."""
        response = client.get("/api/user/profile", headers=USER_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user_123"
        assert data["email"] == "candidate@mockinterview.ai"
        assert data["role"] == "USER"
        assert "Nguyễn Văn Ứng Viên" in data["full_name"]

    def test_update_profile_happy_path(self, client):
        """Happy Path: Cập nhật họ tên và số điện thoại."""
        payload = {
            "full_name": "Nguyễn Thành Đạt",
            "phone_number": "0988776655",
        }
        response = client.patch("/api/user/profile", json=payload, headers=USER_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Nguyễn Thành Đạt"
        assert data["phone_number"] == "0988776655"

    def test_update_profile_boundary_name_too_short(self, client):
        """Boundary/Validation: Họ tên < 2 ký tự vi phạm min_length=2 trả về 422."""
        payload = {"full_name": "A"}
        response = client.patch("/api/user/profile", json=payload, headers=USER_HEADERS)
        assert response.status_code == 422

    def test_update_profile_xss_payload(self, client):
        """Security: Input họ tên chứa thẻ script độc hại được lưu an toàn."""
        payload = {"full_name": "<script>alert('pwned')</script>"}
        response = client.patch("/api/user/profile", json=payload, headers=USER_HEADERS)
        assert response.status_code == 200
        assert "<script>" in response.json()["full_name"]


class TestChangePasswordAPI:
    """Kiểm thử đổi mật khẩu (/api/user/change-password)."""

    def test_change_password_happy_path(self, client, db_session):
        """Happy Path: Đổi mật khẩu thành công khi nhập đúng mật khẩu hiện tại."""
        payload = {
            "current_password": "User@123456",
            "new_password": "NewSecretPassword@2026",
        }
        response = client.post("/api/user/change-password", json=payload, headers=USER_HEADERS)
        assert response.status_code == 200
        assert "thành công" in response.json()["message"]

        # Kiểm tra mật khẩu mới đã được băm an toàn trong DB
        user = db_session.query(models.User).filter(models.User.id == "user_123").first()
        assert verify_password("NewSecretPassword@2026", user.hashed_password) is True

    def test_change_password_wrong_current_password(self, client):
        """Failure Mode: Nhập sai mật khẩu hiện tại trả về 400 Bad Request."""
        payload = {
            "current_password": "WrongPassword@999",
            "new_password": "NewSecretPassword@2026",
        }
        response = client.post("/api/user/change-password", json=payload, headers=USER_HEADERS)
        assert response.status_code == 400
        assert "không chính xác" in response.json()["detail"]

    def test_change_password_same_as_old_password(self, client):
        """Failure Mode: Mật khẩu mới trùng mật khẩu cũ trả về 400 Bad Request."""
        payload = {
            "current_password": "User@123456",
            "new_password": "User@123456",
        }
        response = client.post("/api/user/change-password", json=payload, headers=USER_HEADERS)
        assert response.status_code == 400
        assert "không được trùng" in response.json()["detail"]

    def test_change_password_boundary_new_password_too_short(self, client):
        """Boundary/Validation: Mật khẩu mới < 8 ký tự vi phạm min_length=8 trả về 422."""
        payload = {
            "current_password": "User@123456",
            "new_password": "short",
        }
        response = client.post("/api/user/change-password", json=payload, headers=USER_HEADERS)
        assert response.status_code == 422

    def test_change_password_boundary_empty_new_password(self, client):
        """Boundary/Validation: Mật khẩu mới chuỗi rỗng trả về 422."""
        payload = {
            "current_password": "User@123456",
            "new_password": "",
        }
        response = client.post("/api/user/change-password", json=payload, headers=USER_HEADERS)
        assert response.status_code == 422

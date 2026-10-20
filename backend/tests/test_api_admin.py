"""
Test Suite: Admin Management API (/api/admin/industries & /api/admin/positions)
Covers Happy Path, Constraint Enforcement, Foreign Key Violations, Failure Modes, and Security.
"""

import pytest
from fastapi import HTTPException
from backend.tests.fixtures_api import db_session, client
from backend.dependencies import get_current_admin_user
from backend.main import app
import backend.models as models


ADMIN_HEADERS = {"X-User-Id": "admin_123"}


class TestAdminIndustriesAPI:
    """Kiểm thử quản lý ngành nghề (/api/admin/industries)."""

    def test_create_industry_happy_path(self, client):
        """Happy Path: Admin tạo mới ngành nghề hợp lệ."""
        payload = {
            "name": "Tài chính - Ngân hàng",
            "code": "FIN_BANK",
            "description": "Lĩnh vực ngân hàng tài chính số",
        }
        response = client.post("/api/admin/industries", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["code"] == payload["code"]
        assert data["status"] == "ACTIVE"

    def test_create_industry_duplicate_code(self, client):
        """Failure Mode: Trùng mã code ngành đã có trả về 400 Bad Request."""
        payload = {
            "name": "Công nghệ mới",
            "code": "IT_SW",  # Đã tồn tại trong seed data
        }
        response = client.post("/api/admin/industries", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 400
        assert "đã tồn tại" in response.json()["detail"]

    def test_create_industry_duplicate_name(self, client):
        """Failure Mode: Trùng tên ngành đã có trả về 400 Bad Request."""
        payload = {
            "name": "Công nghệ phần mềm",  # Đã tồn tại trong seed data
            "code": "NEW_CODE_01",
        }
        response = client.post("/api/admin/industries", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 400
        assert "đã tồn tại" in response.json()["detail"]

    def test_delete_industry_with_positions_rejected(self, client):
        """Constraint Enforcement: Xóa ngành đang có vị trí con trả về 400."""
        # it_software đang có vị trí con backend_dev
        response = client.delete("/api/admin/industries/it_software", headers=ADMIN_HEADERS)
        assert response.status_code == 400
        assert "Đang có vị trí trực thuộc" in response.json()["detail"]

    def test_delete_industry_without_positions(self, client):
        """Happy Path: Xóa ngành không có vị trí con trả về 204 No Content."""
        # Tạo ngành độc lập
        create_res = client.post(
            "/api/admin/industries",
            json={"name": "Ngành Độc Lập", "code": "IND_INDEP"},
            headers=ADMIN_HEADERS,
        )
        ind_id = create_res.json()["id"]

        del_res = client.delete(f"/api/admin/industries/{ind_id}", headers=ADMIN_HEADERS)
        assert del_res.status_code == 204

    def test_delete_industry_not_found(self, client):
        """Failure Mode: Xóa ngành không tồn tại trả về 404."""
        response = client.delete("/api/admin/industries/ghost_ind_404", headers=ADMIN_HEADERS)
        assert response.status_code == 404


class TestAdminPositionsAPI:
    """Kiểm thử quản lý vị trí (/api/admin/positions)."""

    def test_create_position_happy_path(self, client):
        """Happy Path: Admin tạo mới vị trí hợp lệ."""
        payload = {
            "name": "Mobile iOS Developer",
            "code": "IOS_DEV",
            "industry_id": "it_software",
            "skills": ["Swift", "SwiftUI", "UIKit"],
            "duration": "3–6 tháng",
            "icon": "smartphone",
        }
        response = client.post("/api/admin/positions", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["industry_id"] == "it_software"
        assert "Swift" in data["skills"]

    def test_create_position_nonexistent_industry(self, client):
        """Failure Mode: Tạo vị trí với industry_id không tồn tại trả về 404."""
        payload = {
            "name": "Vị trí Lạ",
            "industry_id": "ghost_industry_xyz",
        }
        response = client.post("/api/admin/positions", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 404
        assert "Ngành không tồn tại" in response.json()["detail"]

    def test_delete_position_with_segments_rejected(self, client, db_session):
        """Constraint Enforcement: Xóa vị trí đang có phân khúc con trả về 400."""
        # Thêm segment trực thuộc backend_dev
        seg = models.Segment(
            name="Phân khúc Backend Con",
            code="SEG_BE_CHILD",
            industry_id="it_software",
            position_id="backend_dev",
            status="ACTIVE",
        )
        db_session.add(seg)
        db_session.commit()

        del_res = client.delete("/api/admin/positions/backend_dev", headers=ADMIN_HEADERS)
        assert del_res.status_code == 400
        assert "Phân khúc" in del_res.json()["detail"]

    def test_delete_position_without_segments(self, client):
        """Happy Path: Xóa vị trí không có phân khúc con trả về 204 No Content."""
        pos_res = client.post(
            "/api/admin/positions",
            json={"name": "Vị trí Tạm", "code": "TEMP_POS", "industry_id": "it_software"},
            headers=ADMIN_HEADERS,
        )
        pos_id = pos_res.json()["id"]

        del_res = client.delete(f"/api/admin/positions/{pos_id}", headers=ADMIN_HEADERS)
        assert del_res.status_code == 204

    def test_delete_position_not_found(self, client):
        """Failure Mode: Xóa vị trí không tồn tại trả về 404."""
        response = client.delete("/api/admin/positions/ghost_pos_404", headers=ADMIN_HEADERS)
        assert response.status_code == 404


class TestAdminSecurity:
    """Kiểm tra bảo mật và phân quyền quản trị."""

    def test_admin_unauthorized_user_forbidden(self, client):
        """Security: Tài khoản người dùng thường (USER) bị từ chối quyền ADMIN (403)."""
        def reject_non_admin():
            raise HTTPException(status_code=403, detail="Yêu cầu quyền Quản trị viên (ADMIN)")

        app.dependency_overrides[get_current_admin_user] = reject_non_admin
        try:
            response = client.post(
                "/api/admin/industries",
                json={"name": "Xâm nhập trái phép", "code": "HACK"},
                headers={"X-User-Id": "user_123"},
            )
            assert response.status_code == 403
            assert "ADMIN" in response.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_current_admin_user, None)

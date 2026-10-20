"""
Test Suite: Segments CRUD API (/api/segments)
Covers Happy Path, Duplicate Constraints, Filtering/Search, Failure Modes, and Security.
"""

import pytest
from backend.tests.fixtures_api import db_session, client


class TestSegmentsCRUD:
    """Kiểm thử CRUD phân khúc chuyên môn (/api/segments)."""

    def test_create_segment_happy_path(self, client):
        """Happy Path: Tạo mới segment hợp lệ."""
        payload = {
            "name": "Backend Python FastAPI",
            "code": "SEG_BE_PY",
            "industry_id": "it_software",
            "position_id": "backend_dev",
            "description": "Chuyên môn lập trình dịch vụ backend bằng Python",
            "sort_order": 1,
            "status": "ACTIVE",
        }
        response = client.post("/api/segments", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["code"] == payload["code"]
        assert "id" in data

    def test_create_segment_duplicate_name_same_position(self, client):
        """Failure Mode: Trùng tên trong cùng vị trí trả về 400 Bad Request."""
        payload1 = {
            "name": "Frontend React",
            "code": "SEG_FE_1",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        }
        res1 = client.post("/api/segments", json=payload1)
        assert res1.status_code == 201

        payload2 = {
            "name": "Frontend React",
            "code": "SEG_FE_2",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        }
        res2 = client.post("/api/segments", json=payload2)
        assert res2.status_code == 400
        assert "đã tồn tại" in res2.json()["detail"]

    def test_create_segment_duplicate_code(self, client):
        """Failure Mode: Trùng mã phân khúc (code) trả về 400 Bad Request."""
        payload1 = {
            "name": "DevOps AWS",
            "code": "SEG_DEVOPS_SAME",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        }
        res1 = client.post("/api/segments", json=payload1)
        assert res1.status_code == 201

        payload2 = {
            "name": "DevOps GCP",
            "code": "SEG_DEVOPS_SAME",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        }
        res2 = client.post("/api/segments", json=payload2)
        assert res2.status_code == 400
        assert "đã tồn tại" in res2.json()["detail"]

    def test_get_segments_list_and_filter(self, client):
        """Happy Path: Lọc segments theo industryId và positionId."""
        client.post("/api/segments", json={
            "name": "Segment A",
            "code": "SEG_A",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        })
        client.post("/api/segments", json={
            "name": "Segment B",
            "code": "SEG_B",
            "industry_id": "it_software",
            "position_id": "other_pos",
        })

        res = client.get("/api/segments?positionId=backend_dev")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert all(s["position_id"] == "backend_dev" for s in data)

    def test_get_segments_search(self, client):
        """Happy Path: Tìm kiếm segment theo từ khóa tên hoặc mã."""
        client.post("/api/segments", json={
            "name": "Phân khúc Trí tuệ Nhân tạo",
            "code": "SEG_AI_SPECIAL",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        })
        res = client.get("/api/segments?search=Trí tuệ")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert "Trí tuệ Nhân tạo" in data[0]["name"]

    def test_get_segment_by_id_happy_path(self, client):
        """Happy Path: Lấy chi tiết segment qua ID."""
        create_res = client.post("/api/segments", json={
            "name": "Segment Chi Tiết",
            "code": "SEG_DETAIL",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        })
        seg_id = create_res.json()["id"]

        get_res = client.get(f"/api/segments/{seg_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Segment Chi Tiết"

    def test_get_segment_by_id_not_found(self, client):
        """Failure Mode: Lấy segment không tồn tại trả về 404."""
        response = client.get("/api/segments/non_existent_seg_404")
        assert response.status_code == 404

    def test_update_segment_happy_path(self, client):
        """Happy Path: Cập nhật thông tin segment qua PATCH."""
        create_res = client.post("/api/segments", json={
            "name": "Segment Cũ",
            "code": "SEG_UPDATE",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        })
        seg_id = create_res.json()["id"]

        update_payload = {"name": "Segment Mới Đã Sửa", "description": "Mô tả mới"}
        update_res = client.patch(f"/api/segments/{seg_id}", json=update_payload)
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Segment Mới Đã Sửa"
        assert update_res.json()["description"] == "Mô tả mới"

    def test_update_segment_not_found(self, client):
        """Failure Mode: Cập nhật segment không tồn tại trả về 404."""
        response = client.patch("/api/segments/ghost_id", json={"name": "Test"})
        assert response.status_code == 404

    def test_delete_segment_happy_path(self, client):
        """Happy Path: Xóa mềm segment trả về 204 No Content."""
        create_res = client.post("/api/segments", json={
            "name": "Segment Để Xóa",
            "code": "SEG_TO_DELETE",
            "industry_id": "it_software",
            "position_id": "backend_dev",
        })
        seg_id = create_res.json()["id"]

        del_res = client.delete(f"/api/segments/{seg_id}")
        assert del_res.status_code == 204

        # Sau khi xóa mềm, không tìm thấy qua ID
        get_res = client.get(f"/api/segments/{seg_id}")
        assert get_res.status_code == 404

    def test_delete_segment_not_found(self, client):
        """Failure Mode: Xóa segment không tồn tại trả về 404."""
        response = client.delete("/api/segments/ghost_del_404")
        assert response.status_code == 404

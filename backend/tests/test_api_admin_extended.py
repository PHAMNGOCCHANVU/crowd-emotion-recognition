import pytest
from fastapi import HTTPException
from backend.tests.fixtures_api import client, db_session
from backend.dependencies import get_current_admin_user
from backend.main import app
import backend.models as models

ADMIN_HEADERS = {"X-User-Id": "admin_123"}


def test_admin_dashboard_stats(client):
    response = client.get("/api/admin/dashboard/stats", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_sessions" in data
    assert "completion_rate" in data
    assert "average_score" in data
    assert "recent_sessions" in data
    assert isinstance(data["recent_sessions"], list)


def test_admin_industries_crud(client):
    # 1. Get industries
    res = client.get("/api/admin/industries", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    industries = res.json()
    assert isinstance(industries, list)
    if industries:
        ind = industries[0]
        assert "position_count" in ind

        # 2. Patch industry
        patch_res = client.patch(
            f"/api/admin/industries/{ind['id']}",
            json={"name": f"{ind['name']} Updated"},
            headers=ADMIN_HEADERS,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["name"] == f"{ind['name']} Updated"

        # Revert back
        client.patch(
            f"/api/admin/industries/{ind['id']}",
            json={"name": ind["name"]},
            headers=ADMIN_HEADERS,
        )


def test_admin_positions_crud(client):
    # 1. Get positions
    res = client.get("/api/admin/positions", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    positions = res.json()
    assert isinstance(positions, list)
    assert len(positions) > 0
    pos = positions[0]
    assert "industry_name" in pos
    assert "question_count" in pos

    # 2. Patch position
    patch_res = client.patch(
        f"/api/admin/positions/{pos['id']}",
        json={"duration": "4–8 tháng"},
        headers=ADMIN_HEADERS,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["duration"] == "4–8 tháng"


def test_admin_questions_crud(client):
    # Lấy 1 position hợp lệ
    pos_res = client.get("/api/admin/positions", headers=ADMIN_HEADERS)
    pos_id = pos_res.json()[0]["id"]

    # 1. Create Question
    create_payload = {
        "position_id": pos_id,
        "category": "Chuyên môn",
        "question_text": "Câu hỏi test CRUD tự động của Admin",
        "time_limit_seconds": 90,
        "level": "junior",
        "levels": ["junior", "mid"],
    }
    create_res = client.post("/api/admin/questions", json=create_payload, headers=ADMIN_HEADERS)
    assert create_res.status_code == 201
    created_q = create_res.json()
    assert created_q["id"].startswith("q_admin_")
    assert created_q["question_text"] == create_payload["question_text"]
    q_id = created_q["id"]

    # 2. Patch Question
    patch_res = client.patch(
        f"/api/admin/questions/{q_id}",
        json={"question_text": "Câu hỏi test đã được sửa"},
        headers=ADMIN_HEADERS,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["question_text"] == "Câu hỏi test đã được sửa"

    # 3. Delete Question
    del_res = client.delete(f"/api/admin/questions/{q_id}", headers=ADMIN_HEADERS)
    assert del_res.status_code == 204

    # 4. Verify Deleted
    patch_again = client.patch(
        f"/api/admin/questions/{q_id}",
        json={"question_text": "Non-existent"},
        headers=ADMIN_HEADERS,
    )
    assert patch_again.status_code == 404


def test_admin_users_and_sessions(client):
    # 1. Get Users
    users_res = client.get("/api/admin/users", headers=ADMIN_HEADERS)
    assert users_res.status_code == 200
    users = users_res.json()
    assert isinstance(users, list)

    # 2. Search Users
    search_res = client.get("/api/admin/users?search=candidate", headers=ADMIN_HEADERS)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert isinstance(search_data, list)

    if users:
        target_user = users[0]
        # 3. Get User Sessions
        sess_res = client.get(f"/api/admin/users/{target_user['id']}/sessions", headers=ADMIN_HEADERS)
        assert sess_res.status_code == 200
        assert isinstance(sess_res.json(), list)


def test_admin_delete_user(client, db_session):
    # 1. Delete non-existent user returns 404
    res_404 = client.delete("/api/admin/users/non_existent_user_999", headers=ADMIN_HEADERS)
    assert res_404.status_code == 404

    # 2. Cannot delete an ADMIN user
    admin_u = models.User(
        id="usr_admin_victim",
        email="admin_victim@example.com",
        full_name="Admin Victim",
        role="ADMIN",
    )
    db_session.add(admin_u)
    db_session.commit()

    del_admin_res = client.delete("/api/admin/users/usr_admin_victim", headers=ADMIN_HEADERS)
    assert del_admin_res.status_code == 400
    assert "Quản trị viên" in del_admin_res.json()["detail"]

    # 3. Delete regular user and cascade related data
    candidate_u = models.User(
        id="usr_candidate_del",
        email="candidate_del@example.com",
        full_name="Candidate Delete Me",
        role="USER",
    )
    db_session.add(candidate_u)
    db_session.commit()

    session_obj = models.InterviewSession(
        id="sess_candidate_del",
        user_id="usr_candidate_del",
        role_name="Backend Developer",
        overall_score=8.5,
    )
    db_session.add(session_obj)
    db_session.commit()

    # Verify user exists
    get_u = client.get("/api/admin/users?search=Candidate Delete Me", headers=ADMIN_HEADERS)
    assert len(get_u.json()) == 1

    # Delete user
    del_res = client.delete("/api/admin/users/usr_candidate_del", headers=ADMIN_HEADERS)
    assert del_res.status_code == 204

    # Verify deleted
    get_u_again = client.get("/api/admin/users?search=Candidate Delete Me", headers=ADMIN_HEADERS)
    assert len(get_u_again.json()) == 0


def test_admin_extended_security_forbidden(client):
    """Kiểm tra quyền ADMIN trên các endpoint mở rộng mới: 403 Forbidden nếu không phải ADMIN."""
    def reject_non_admin():
        raise HTTPException(status_code=403, detail="Yêu cầu quyền Quản trị viên (ADMIN)")

    app.dependency_overrides[get_current_admin_user] = reject_non_admin
    try:
        # Dashboard stats
        r1 = client.get("/api/admin/dashboard/stats", headers={"X-User-Id": "user_normal"})
        assert r1.status_code == 403

        # Questions CRUD
        r2 = client.post("/api/admin/questions", json={"question_text": "Hack"}, headers={"X-User-Id": "user_normal"})
        assert r2.status_code == 403

        # Users list
        r3 = client.get("/api/admin/users", headers={"X-User-Id": "user_normal"})
        assert r3.status_code == 403

        # Delete user
        r4 = client.delete("/api/admin/users/user_target", headers={"X-User-Id": "user_normal"})
        assert r4.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_admin_user, None)


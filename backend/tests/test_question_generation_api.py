"""Preview and session reuse must preserve exact generated questions and JD context."""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.api import questions, sessions
from backend.database import Base, get_db
from backend.services.ai_contracts import ServiceError
from backend.tests.test_question_generation import JD, generated_content


@pytest.fixture
def generation_api(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app = FastAPI()
    app.include_router(questions.router)
    app.include_router(sessions.router)
    app.dependency_overrides[get_db] = lambda: db
    operation = Mock(return_value={**generated_content(), "metadata": {
        "provider": "gemini", "model": "gemini-3.5-flash-lite", "is_mock": False,
        "fallback_reason": None, "latency_ms": 10,
    }})
    monkeypatch.setattr(questions, "generate_interview_questions", operation)
    with TestClient(app) as client:
        yield client, db, operation
    db.close()
    engine.dispose()


def generate(client):
    return client.post("/api/questions/generate", json={
        "role_name": "Backend Developer", "level": "mid", "jd_text": JD,
    })


def test_preview_then_start_uses_exact_snapshot_without_another_model_call(generation_api):
    client, db, operation = generation_api
    response = generate(client)
    assert response.status_code == 201
    preview = response.json()
    assert preview["total"] == 4
    assert [q["order_index"] for q in preview["questions"]] == [1, 2, 3, 4]
    assert all(q["time_limit_seconds"] == 120 for q in preview["questions"])
    assert db.query(models.Question).count() == 0  # No JD-specific questions in the shared bank.
    assert db.query(models.GeneratedQuestionSet).count() == 1
    assert db.query(models.InterviewSession).count() == 0

    response = client.post("/api/sessions/start", json={
        "role_name": "Backend Developer", "generated_set_id": preview["generated_set_id"],
    })
    assert response.status_code == 201
    session = response.json()
    assert session["level"] == "mid"  # Missing level/JD are restored from the saved preview.
    assert session["generated_set_id"] == preview["generated_set_id"]
    expected = [q["question_text"] for q in preview["questions"]]
    assert [q["question_text"] for q in session["questions"]] == expected
    stored = db.get(models.InterviewSession, session["session_id"])
    assert stored.jd_text == JD
    details = db.query(models.SessionDetail).filter_by(session_id=stored.id).order_by(models.SessionDetail.order_index).all()
    assert [d.question_text for d in details] == expected
    assert all(d.status == "PENDING" for d in details)
    operation.assert_called_once()


def test_each_generation_creates_a_new_preview(generation_api):
    client, db, operation = generation_api
    first, second = generate(client).json(), generate(client).json()
    assert first["generated_set_id"] != second["generated_set_id"]
    assert first["questions"][0]["id"] != second["questions"][0]["id"]
    assert db.query(models.GeneratedQuestionSet).count() == operation.call_count == 2


@pytest.mark.parametrize("change", [
    {"role_name": "Marketing"}, {"level": "senior"}, {"jd_text": JD + " Yêu cầu khác."},
])
def test_changed_context_rejected_before_creating_session(generation_api, change):
    client, db, operation = generation_api
    preview = generate(client).json()
    result = client.post("/api/sessions/start", json={
        "role_name": "Backend Developer", "generated_set_id": preview["generated_set_id"], **change,
    })
    assert result.status_code == 409
    assert db.query(models.InterviewSession).count() == 0
    assert db.query(models.User).count() == 0


def test_missing_set_and_conflicting_sources_cannot_fall_back(generation_api):
    client, db, operation = generation_api
    payload = {"role_name": "Backend Developer", "generated_set_id": str(uuid4())}
    assert client.post("/api/sessions/start", json=payload).status_code == 404
    assert client.post("/api/sessions/start", json={**payload, "question_ids": ["bank-question"]}).status_code == 422
    assert client.post("/api/sessions/start", json={**payload, "generated_set_id": "invalid"}).status_code == 422
    assert db.query(models.InterviewSession).count() == 0
    operation.assert_not_called()


@pytest.mark.parametrize("error,status", [
    ("missing_question_generation_key", 503), ("question_generation_unavailable", 503),
    ("question_generation_rate_limited", 429), ("invalid_generated_questions", 502),
])
def test_generation_failures_do_not_save_mock_or_partial_sets(generation_api, error, status):
    client, db, operation = generation_api
    operation.side_effect = ServiceError(error, "Thông báo đã làm sạch.")
    response = generate(client)
    assert response.status_code == status
    assert response.json()["detail"]["code"] == error
    assert db.query(models.GeneratedQuestionSet).count() == 0


def test_missing_jd_rejected_and_legacy_session_still_works(generation_api):
    client, db, operation = generation_api
    assert client.post("/api/questions/generate", json={"role_name": "Backend Developer", "level": "mid"}).status_code == 422
    response = client.post("/api/sessions/start", json={"role_name": "Software Engineer"})
    assert response.status_code == 201
    assert response.json()["total_questions"] == 3
    operation.assert_not_called()

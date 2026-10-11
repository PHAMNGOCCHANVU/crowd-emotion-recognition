"""Exercise AI-01's worker/database/API with real service validation and stub FER."""

import importlib
import importlib.util
import json
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock
from pathlib import Path

import pytest
from google.genai import types
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Load the pure analytics module without ai_core.__init__ eagerly importing Torch.
_spec = importlib.util.spec_from_file_location(
    "interview_analytics_standalone", Path(__file__).resolve().parents[1] / "ai_core/interview_analytics.py",
)
_analytics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_analytics)
InterviewEmotionAnalytics = _analytics.InterviewEmotionAnalytics
from backend.database import Base
from backend.models import InterviewSession, SessionDetail
from backend.services.ai_contracts import AISettings, ServiceError
from backend.services.llm_service import evaluate_interview_answer_llm


@pytest.fixture
def pipeline(monkeypatch):
    # Only face inference is stubbed; use A's real analytics output shape.
    fer = ModuleType("backend.services.fer_service")
    fer.analyze_interview_video_fer = lambda path: InterviewEmotionAnalytics().analyze_interview_sequence([
        {"frame_idx": 0, "emotion": "Normal", "confidence": 0.9},
    ])
    monkeypatch.setitem(sys.modules, "backend.services.fer_service", fer)
    worker = importlib.import_module("backend.services.pipeline_worker")
    monkeypatch.setattr(worker, "analyze_interview_video_fer", fer.analyze_interview_video_fer)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(worker, "SessionLocal", factory)
    with factory() as db:
        db.add(InterviewSession(id="session", role_name="Engineer", status="IN_PROGRESS"))
        db.add_all([
            SessionDetail(id="one", session_id="session", order_index=1, question_text="First question?",
                          status="COMPLETED", content_score=90, confidence_score=80, stress_score=20,
                          ai_feedback={"metadata": {"is_mock": False}}),
            SessionDetail(id="two", session_id="session", order_index=2, question_text="Second question?",
                          status="PROCESSING"),
        ])
        db.commit()
    speech = {"transcript": "Ừm, tôi tối ưu truy vấn.", "filler_words_count": 1,
              "words": [{"word": "Ừm,", "start": 0, "end": 0.3}],
              "metadata": {"provider": "groq", "is_mock": False}}
    monkeypatch.setattr(worker, "transcribe_audio_whisper", lambda path: speech)
    client = Mock()
    client.models.generate_content.return_value = types.GenerateContentResponse(
        candidates=[types.Candidate(finish_reason="STOP", content=types.Content(parts=[types.Part(text=json.dumps({
            "content_score": 80, "content_critique": "Có hành động, cần bổ sung kết quả.",
            "delivery_critique": "Một từ đệm.", "suggested_answer": "Bổ sung kết quả thực tế.",
        }))]))],
    )
    monkeypatch.setattr(worker, "evaluate_interview_answer_llm", lambda **kwargs: evaluate_interview_answer_llm(
        **kwargs, settings=AISettings(), client=client,
    ))
    yield SimpleNamespace(worker=worker, factory=factory, speech=speech, client=client)
    engine.dispose()


def test_worker_keeps_ai01_contract_and_timestamps(pipeline, sample_audio):
    pipeline.worker.process_answer_in_background("session", 2, str(sample_audio))
    assert not sample_audio.exists()
    with pipeline.factory() as db:
        detail = db.get(SessionDetail, "two")
        assert detail.status == "COMPLETED"
        assert detail.content_score == 80
        assert detail.ai_feedback["word_timestamps"] == pipeline.speech["words"]
        session = db.get(InterviewSession, "session")
        assert session.status == "COMPLETED"
        assert session.overall_score == 84.0  # content avg 85; confidence avg 82.5
    payload = json.loads(pipeline.client.models.generate_content.call_args.kwargs["contents"])
    assert payload["emotion_metrics"]["dominant_emotion"] == "Normal"
    assert payload["emotion_metrics"]["emotion_timeline"][0]["is_stress"] is False


def test_mock_fallback_excluded_from_worker_and_results(pipeline, sample_audio):
    pipeline.speech["metadata"]["is_mock"] = True
    pipeline.worker.process_answer_in_background("session", 2, str(sample_audio))
    assert not sample_audio.exists()
    pipeline.client.models.generate_content.assert_not_called()
    endpoints = importlib.import_module("backend.api.sessions")
    with pipeline.factory() as db:
        detail = db.get(SessionDetail, "two")
        assert detail.status == "FAILED"
        assert detail.content_score is None
        assert detail.ai_feedback["metadata"]["is_mock"]
        report = endpoints.get_session_results("session", db)
        assert report.summary.content_score_avg == 90
        assert report.summary.overall_score == 86
        status = endpoints.get_session_status("session", db)
        assert status.is_fully_completed
        assert status.overall_status == "FAILED"


def test_service_error_cleans_video_and_clears_stale_score(pipeline, sample_audio, monkeypatch):
    with pipeline.factory() as db:
        item = db.get(SessionDetail, "two")
        item.status = "COMPLETED"
        item.content_score = 100
        db.commit()

    def fail(path):
        raise ServiceError("speech_api_error", "Whisper HTTP 401")

    monkeypatch.setattr(pipeline.worker, "transcribe_audio_whisper", fail)
    pipeline.worker.process_answer_in_background("session", 2, str(sample_audio))
    assert not sample_audio.exists()
    with pipeline.factory() as db:
        item = db.get(SessionDetail, "two")
        assert item.status == "FAILED" and item.content_score is None
        assert item.ai_feedback["metadata"]["error_code"] == "speech_api_error"
        assert db.get(InterviewSession, "session").overall_score == 86


def test_missing_question_still_cleans_video(pipeline, sample_audio):
    pipeline.worker.process_answer_in_background("session", 99, str(sample_audio))
    assert not sample_audio.exists()


def test_original_positional_llm_signature_is_supported():
    feedback = evaluate_interview_answer_llm("Question?", "Ừm, answer", 80, 20, 1, "Engineer", settings=AISettings(mode="mock"))
    assert feedback["metadata"]["is_mock"]

import os
import logging
from ..database import SessionLocal
from ..models import InterviewSession, SessionDetail
from .fer_service import analyze_interview_video_fer
from .speech_service import transcribe_audio_whisper
from .llm_service import evaluate_interview_answer_llm
from .firebase_storage import upload_interview_video_to_firebase
from .ai_contracts import ServiceError

logger = logging.getLogger(__name__)


def _update_summary(db, session):
    """Only complete, non-mock answers contribute to session scores."""
    if session is None:
        return
    details = db.query(SessionDetail).filter(SessionDetail.session_id == session.id).all()
    completed = [d for d in details if d.status == "COMPLETED"
                 and not (d.ai_feedback or {}).get("metadata", {}).get("is_mock", False)]
    if completed:
        count = len(completed)
        avg_conf = sum(d.confidence_score or 0 for d in completed) / count
        avg_stress = sum(d.stress_score or 0 for d in completed) / count
        avg_content = sum(d.content_score or 0 for d in completed) / count
        session.confidence_avg = round(avg_conf, 1)
        session.stress_avg = round(avg_stress, 1)
        session.overall_score = round(avg_content * 0.6 + avg_conf * 0.4, 1)
    else:
        session.confidence_avg = session.stress_avg = session.overall_score = 0.0
    if details and all(d.status in {"COMPLETED", "FAILED"} for d in details):
        session.status = "FAILED" if any(d.status == "FAILED" for d in details) else "COMPLETED"
    else:
        session.status = "IN_PROGRESS"


def process_answer_in_background(
    session_id: str,
    order_index: int,
    temp_video_path: str,
):
    """
    Tác vụ chạy ngầm của FastAPI BackgroundTasks:
    1. Chạy FER trích xuất cảm xúc từ video.
    2. Chạy Groq Whisper API trích transcript & đếm từ đệm.
    3. Chạy Gemini LLM chấm điểm & sinh nhận xét.
    4. Cập nhật kết quả vào SQLite Database.
    5. Xóa bỏ file video tạm để giải phóng ổ cứng (Ephemeral Processing).
    """
    db = SessionLocal()
    detail = None
    session = None
    try:
        detail = (
            db.query(SessionDetail)
            .filter(
                SessionDetail.session_id == session_id,
                SessionDetail.order_index == order_index,
            )
            .first()
        )
        if not detail:
            print(f"[Pipeline Worker Warning] Không tìm thấy detail cho session {session_id}, order {order_index}")
            return

        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session is None:
            raise ServiceError("missing_session", "Không tìm thấy phiên phỏng vấn.")
        role_name = session.role_name if session else "General"

        # 1. Trích xuất FER (Thị giác & Phong thái)
        fer_results = analyze_interview_video_fer(temp_video_path)
        confidence_score = fer_results.get("confidence_score", 75.0)
        stress_score = fer_results.get("stress_score", 15.0)
        emotion_timeline = fer_results.get("emotion_timeline", [])

        # 2. Trích xuất Whisper (Lời nói & Từ ngập ngừng)
        try:
            speech_results = transcribe_audio_whisper(temp_video_path)
        except ServiceError as se:
            logger.warning("Whisper transcription error (%s): %s", se.code, se)
            if se.code in ("invalid_speech_response", "invalid_duration", "invalid_media"):
                speech_results = {
                    "transcript": "",
                    "filler_words_count": 0,
                    "words": [],
                    "metadata": {
                        "provider": "local",
                        "model": "whisper-fallback",
                        "is_mock": False,
                        "fallback_reason": se.code,
                        "latency_ms": 0.0,
                    },
                }
            else:
                raise
        transcript = speech_results.get("transcript", "")
        filler_words_count = speech_results.get("filler_words_count", 0)

        # 3. Đánh giá LLM (Nội dung & Tổng hợp phong thái)
        llm_feedback = evaluate_interview_answer_llm(
            question_text=detail.question_text,
            transcript=transcript,
            confidence_score=confidence_score,
            stress_score=stress_score,
            filler_words_count=filler_words_count,
            role_name=role_name,
            emotion_metrics=fer_results,
            speech_is_mock=speech_results.get("metadata", {}).get("is_mock", False),
        )
        is_mock = (speech_results.get("metadata", {}).get("is_mock", False)
                   or llm_feedback.get("metadata", {}).get("is_mock", False))
        content_score = llm_feedback["content_score"] if not is_mock else None
        # Preserve word timestamps and provenance without a database migration.
        llm_feedback["speech_metadata"] = speech_results.get("metadata", {})
        llm_feedback["word_timestamps"] = speech_results.get("words", [])

        # 4. Tải video lên Firebase Cloud Storage (nếu có key, ngược lại fallback)
        video_url = upload_interview_video_to_firebase(temp_video_path, session_id, order_index)

        # 5. Cập nhật SessionDetail
        detail.transcript = transcript
        detail.filler_words_count = filler_words_count
        detail.confidence_score = confidence_score
        detail.stress_score = stress_score
        detail.content_score = content_score
        detail.emotion_timeline = emotion_timeline
        detail.ai_feedback = llm_feedback
        detail.video_url = video_url
        detail.status = "FAILED" if is_mock else "COMPLETED"

        # 6. Cập nhật lại điểm trung bình của InterviewSession
        _update_summary(db, session)

        db.commit()
        print(f"[Pipeline Worker] Hoàn thành phân tích câu {order_index} cho session {session_id}")

    except Exception as e:
        db.rollback()
        code = e.code if isinstance(e, ServiceError) else "pipeline_error"
        logger.exception("Interview pipeline failed (%s): %s", code, e)
        if detail:
            detail.status = "FAILED"
            detail.content_score = None
            detail.ai_feedback = {
                "content_critique": "Chưa thể đánh giá câu trả lời. Hãy kiểm tra cấu hình hoặc thử lại.",
                "delivery_critique": "Chưa có nhận xét hoàn chỉnh.",
                "suggested_answer": "",
                "metadata": {"is_mock": False, "error_code": code},
            }
            _update_summary(db, session)
            db.commit()
    finally:
        db.close()
        # 6. TỰ HỦY FILE TẠM TRONG /tmp/ (EPHEMERAL STORAGE)
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                print(f"[Pipeline Worker] Đã xóa file tạm {temp_video_path} thành công.")
            except Exception as e:
                print(f"[Pipeline Worker Warning] Không thể xóa file tạm: {e}")

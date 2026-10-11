import os
import traceback
from ..database import SessionLocal
from ..models import InterviewSession, SessionDetail
from .fer_service import analyze_interview_video_fer
from .speech_service import transcribe_audio_whisper
from .llm_service import evaluate_interview_answer_llm


def process_answer_in_background(
    session_id: str,
    order_index: int,
    temp_video_path: str,
):
    """
    Tác vụ chạy ngầm của FastAPI BackgroundTasks:
    1. Chạy FER trích xuất cảm xúc từ video.
    2. Chạy Whisper API trích transcript & đếm từ đệm.
    3. Chạy Gemini LLM chấm điểm & sinh nhận xét.
    4. Cập nhật kết quả vào SQLite Database.
    5. Xóa bỏ file video tạm để giải phóng ổ cứng (Ephemeral Processing).
    """
    db = SessionLocal()
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
        role_name = session.role_name if session else "General"

        # 1. Trích xuất FER (Thị giác & Phong thái)
        fer_results = analyze_interview_video_fer(temp_video_path)
        confidence_score = fer_results.get("confidence_score", 75.0)
        stress_score = fer_results.get("stress_score", 15.0)
        emotion_timeline = fer_results.get("emotion_timeline", [])

        # 2. Trích xuất Whisper (Lời nói & Từ ngập ngừng)
        speech_results = transcribe_audio_whisper(temp_video_path)
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
        )
        content_score = llm_feedback.get("content_score", 80.0)

        # 4. Cập nhật SessionDetail
        detail.transcript = transcript
        detail.filler_words_count = filler_words_count
        detail.confidence_score = confidence_score
        detail.stress_score = stress_score
        detail.content_score = content_score
        detail.emotion_timeline = emotion_timeline
        detail.ai_feedback = llm_feedback
        detail.status = "COMPLETED"

        # 5. Cập nhật lại điểm trung bình của InterviewSession
        all_details = db.query(SessionDetail).filter(SessionDetail.session_id == session_id).all()
        completed = [d for d in all_details if d.status == "COMPLETED"]
        if completed:
            avg_conf = sum(d.confidence_score for d in completed) / len(completed)
            avg_stress = sum(d.stress_score for d in completed) / len(completed)
            avg_content = sum(d.content_score for d in completed) / len(completed)
            overall = round(avg_content * 0.6 + avg_conf * 0.4, 1)

            session.confidence_avg = round(avg_conf, 1)
            session.stress_avg = round(avg_stress, 1)
            session.overall_score = overall

            if len(completed) == len(all_details):
                session.status = "COMPLETED"

        db.commit()
        print(f"[Pipeline Worker] Hoàn thành phân tích câu {order_index} cho session {session_id}")

    except Exception as e:
        db.rollback()
        print(f"[Pipeline Worker Error] Lỗi xử lý ngầm: {e}")
        traceback.print_exc()
        if detail:
            detail.status = "FAILED"
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

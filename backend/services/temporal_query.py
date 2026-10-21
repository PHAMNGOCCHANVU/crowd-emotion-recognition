"""
temporal_query.py — Temporal Query Engine for Mock Interview Platform
====================================================================
Module chuyên biệt truy vấn dữ liệu chuỗi thời gian (time-series emotion data)
từ database SQLite / PostgreSQL JSONB để phục vụ Chatbot và Báo cáo.
"""

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from ..models import InterviewSession, SessionDetail

EMOTION_CLASSES = ["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"]


def query_emotion_by_time(
    db: Session,
    session_id: str,
    order_index: int,
    start_second: int,
    end_second: int,
) -> dict[str, Any]:
    """
    Truy vấn diễn biến cảm xúc trong khoảng thời gian [start_second, end_second]
    của câu hỏi có số thứ tự order_index.
    """
    if start_second < 0 or end_second < 0:
        return {"error": "Thời gian truy vấn không hợp lệ (phải >= 0)."}

    if start_second > end_second:
        start_second, end_second = end_second, start_second

    detail = (
        db.query(SessionDetail)
        .filter(
            SessionDetail.session_id == session_id,
            SessionDetail.order_index == order_index,
        )
        .first()
    )

    if not detail:
        return {"error": f"Không tìm thấy dữ liệu cho câu hỏi số {order_index}."}

    timeline = detail.emotion_timeline or []
    if not timeline:
        return {
            "error": f"Câu hỏi số {order_index} chưa có dữ liệu cảm xúc hoặc đang chờ xử lý.",
            "status": detail.status,
        }

    # Lọc các điểm dữ liệu nằm trong khung thời gian [start_second, end_second]
    filtered_points = [
        point for point in timeline
        if start_second <= point.get("second", 0) <= end_second
    ]

    max_second = max((p.get("second", 0) for p in timeline), default=0)

    if not filtered_points:
        return {
            "warning": (
                f"Không có dữ liệu trong khoảng {start_second}s - {end_second}s. "
                f"Video câu trả lời này dài {max_second} giây."
            ),
            "max_second_available": max_second,
            "data_available": False,
        }

    total_points = len(filtered_points)
    emotions = [p.get("emotion", "Normal") for p in filtered_points]
    confidences = [p.get("confidence", 0.8) for p in filtered_points]
    stress_points = [p for p in filtered_points if p.get("is_stress", False)]

    counts = Counter(emotions)
    distribution = {
        emo: round(counts.get(emo, 0) / total_points, 4)
        for emo in EMOTION_CLASSES
    }

    dominant_emotion = Counter(emotions).most_common(1)[0][0]
    avg_confidence = round(sum(confidences) / total_points, 3)
    stress_ratio = round(len(stress_points) / total_points, 3)

    return {
        "success": True,
        "session_id": session_id,
        "order_index": order_index,
        "question_text": detail.question_text,
        "time_range": f"{start_second}s - {end_second}s",
        "duration_seconds": end_second - start_second,
        "total_data_points": total_points,
        "dominant_emotion": dominant_emotion,
        "emotion_distribution": distribution,
        "average_confidence": avg_confidence,
        "stress_ratio": stress_ratio,
        "stress_count_seconds": len(stress_points),
        "timeline_detail": filtered_points,
    }


def get_session_summary(
    db: Session,
    session_id: str,
    include_timeline: bool = False,
) -> dict[str, Any]:
    """
    Lấy tổng quan kết quả phỏng vấn toàn bộ phiên làm việc.
    """
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id)
        .first()
    )
    if not session:
        return {"error": f"Không tìm thấy phiên phỏng vấn với ID {session_id}."}

    details = (
        db.query(SessionDetail)
        .filter(SessionDetail.session_id == session_id)
        .order_by(SessionDetail.order_index.asc())
        .all()
    )

    questions_summary = []
    total_fillers = 0

    for d in details:
        total_fillers += d.filler_words_count or 0
        q_item = {
            "order_index": d.order_index,
            "question_text": d.question_text,
            "status": d.status,
            "confidence_score": d.confidence_score or 0.0,
            "stress_score": d.stress_score or 0.0,
            "content_score": d.content_score or 0.0,
            "filler_words_count": d.filler_words_count or 0,
            "transcript_snippet": (d.transcript[:120] + "...") if d.transcript and len(d.transcript) > 120 else (d.transcript or ""),
        }
        if include_timeline:
            q_item["emotion_timeline"] = d.emotion_timeline or []
        questions_summary.append(q_item)

    return {
        "success": True,
        "session_id": session.id,
        "role_name": session.role_name,
        "overall_status": session.status,
        "overall_score": session.overall_score or 0.0,
        "confidence_avg": session.confidence_avg or 0.0,
        "stress_avg": session.stress_avg or 0.0,
        "total_filler_words": total_fillers,
        "total_questions": len(details),
        "questions": questions_summary,
    }


def compare_questions(
    db: Session,
    session_id: str,
    question_a: int,
    question_b: int,
) -> dict[str, Any]:
    """
    So sánh các chỉ số cảm xúc và phong thái giữa 2 câu hỏi trong cùng một phiên.
    """
    detail_a = (
        db.query(SessionDetail)
        .filter(
            SessionDetail.session_id == session_id,
            SessionDetail.order_index == question_a,
        )
        .first()
    )
    detail_b = (
        db.query(SessionDetail)
        .filter(
            SessionDetail.session_id == session_id,
            SessionDetail.order_index == question_b,
        )
        .first()
    )

    if not detail_a or not detail_b:
        missing = []
        if not detail_a:
            missing.append(f"câu {question_a}")
        if not detail_b:
            missing.append(f"câu {question_b}")
        return {"error": f"Không tìm thấy {' và '.join(missing)} để so sánh."}

    conf_diff = round((detail_a.confidence_score or 0.0) - (detail_b.confidence_score or 0.0), 1)
    stress_diff = round((detail_a.stress_score or 0.0) - (detail_b.stress_score or 0.0), 1)

    return {
        "success": True,
        "session_id": session_id,
        "question_a": {
            "order_index": question_a,
            "question_text": detail_a.question_text,
            "confidence_score": detail_a.confidence_score or 0.0,
            "stress_score": detail_a.stress_score or 0.0,
            "content_score": detail_a.content_score or 0.0,
            "filler_words_count": detail_a.filler_words_count or 0,
        },
        "question_b": {
            "order_index": question_b,
            "question_text": detail_b.question_text,
            "confidence_score": detail_b.confidence_score or 0.0,
            "stress_score": detail_b.stress_score or 0.0,
            "content_score": detail_b.content_score or 0.0,
            "filler_words_count": detail_b.filler_words_count or 0,
        },
        "comparison_result": {
            "more_confident_question": question_a if conf_diff > 0 else (question_b if conf_diff < 0 else "Ngang nhau"),
            "more_stressed_question": question_a if stress_diff > 0 else (question_b if stress_diff < 0 else "Ngang nhau"),
            "confidence_delta": abs(conf_diff),
            "stress_delta": abs(stress_diff),
        },
    }


def get_candidate_global_summary(db: Session, user_id: str) -> dict[str, Any]:
    """
    Trích xuất tổng hợp quá trình luyện tập phỏng vấn của ứng viên (Global Context).
    """
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            "user_id": user_id,
            "total_sessions": 0,
            "has_data": False,
            "summary_text": "Ứng viên chưa hoàn thành buổi phỏng vấn thử nào.",
            "recent_sessions": [],
        }

    scores = [s.overall_score for s in sessions if s.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    confidences = [s.confidence_avg for s in sessions if s.confidence_avg is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0

    stresses = [s.stress_avg for s in sessions if s.stress_avg is not None]
    avg_stress = round(sum(stresses) / len(stresses), 1) if stresses else 0.0

    roles = [s.role_name for s in sessions if s.role_name]
    latest_role = roles[0] if roles else "Chưa xác định"
    unique_roles = list(dict.fromkeys(roles))

    recent = []
    for s in sessions[:5]:
        recent.append({
            "id": s.id,
            "session_id": s.id,
            "role_name": s.role_name,
            "level": s.level or "fresher",
            "overall_score": round(s.overall_score or 0.0, 1),
            "status": s.status,
            "date": s.created_at.strftime("%d/%m/%Y") if s.created_at else "",
            "created_at": s.created_at.isoformat() if s.created_at else "",
        })

    return {
        "user_id": user_id,
        "total_sessions": total_sessions,
        "has_data": True,
        "average_score": avg_score,
        "average_overall_score": avg_score,
        "average_confidence": avg_confidence,
        "average_stress": avg_stress,
        "latest_role": latest_role,
        "practiced_roles": unique_roles,
        "recent_sessions": recent,
    }


def get_question_critique_data(db: Session, session_id: str, order_index: int) -> dict[str, Any]:
    """
    Lấy chi tiết transcript và nhận xét AI của câu hỏi order_index trong session_id.
    """
    detail = (
        db.query(SessionDetail)
        .filter(
            SessionDetail.session_id == session_id,
            SessionDetail.order_index == order_index,
        )
        .first()
    )
    if not detail:
        return {"error": f"Không tìm thấy câu hỏi số {order_index} trong phiên này."}

    feedback = detail.ai_feedback or {}
    return {
        "success": True,
        "session_id": session_id,
        "order_index": order_index,
        "question_text": detail.question_text,
        "transcript": detail.transcript or "",
        "filler_words_count": detail.filler_words_count or 0,
        "confidence_score": detail.confidence_score or 0.0,
        "stress_score": detail.stress_score or 0.0,
        "content_score": detail.content_score or 0.0,
        "content_critique": feedback.get("content_critique", ""),
        "delivery_critique": feedback.get("delivery_critique", ""),
        "suggested_answer": feedback.get("suggested_answer", ""),
        "content_feedback": feedback.get("content_critique", ""),
        "delivery_feedback": feedback.get("delivery_critique", ""),
        "sample_answer": feedback.get("suggested_answer", ""),
    }


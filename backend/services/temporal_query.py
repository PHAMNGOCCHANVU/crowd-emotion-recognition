"""
temporal_query.py — Temporal Query Engine for Mock Interview Platform
====================================================================
Module chuyên biệt truy vấn dữ liệu chuỗi thời gian (time-series emotion data)
từ database SQLite / PostgreSQL JSONB để phục vụ Chatbot và Báo cáo.
"""

from collections import Counter
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models import InterviewSession, SessionDetail

EMOTION_CLASSES = ["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"]


def query_emotion_by_time(
    db: Session,
    session_id: str,
    order_index: int,
    start_second: int,
    end_second: int,
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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

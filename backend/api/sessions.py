import os
import uuid
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, InterviewSession, SessionDetail
from ..schemas import (
    SessionStartRequest,
    SessionStartResponse,
    AnswerUploadResponse,
    SessionStatusResponse,
    QuestionStatusItem,
    SessionResultResponse,
    SessionSummary,
    QuestionResultDetail,
)
from .questions import get_questions_for_role
from ..services.pipeline_worker import process_answer_in_background

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
def start_interview_session(req: SessionStartRequest, db: Session = Depends(get_db)):
    """
    Khởi tạo phiên phỏng vấn mới, tạo dữ liệu phiên và sinh 3 câu hỏi mẫu.
    """
    user_id = req.user_id or "guest"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=f"{user_id}@mockinterview.local", full_name="Ứng viên Thử nghiệm")
        db.add(user)
        db.commit()

    session_id = str(uuid.uuid4())
    session = InterviewSession(
        id=session_id,
        user_id=user.id,
        role_name=req.role_name,
        jd_text=req.jd_text,
        status="IN_PROGRESS",
    )
    db.add(session)

    # Sinh danh sách câu hỏi
    questions = get_questions_for_role(req.role_name, req.jd_text)
    for q in questions:
        detail = SessionDetail(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question_text=q.question_text,
            order_index=q.order_index,
            status="PENDING",
        )
        db.add(detail)

    db.commit()

    return SessionStartResponse(
        session_id=session_id,
        role_name=req.role_name,
        total_questions=len(questions),
        questions=questions,
        created_at=datetime.utcnow().isoformat(),
    )


@router.post(
    "/{session_id}/questions/{order_index}/answer",
    response_model=AnswerUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_question_answer(
    session_id: str,
    order_index: int,
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Tiếp nhận file video WebM từng câu trả lời:
    - Lưu tạm vào thư mục /tmp/
    - Kích hoạt BackgroundTasks phân tích ngầm
    - Trả ngay mã 202 Accepted cho client trong < 800ms
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên phỏng vấn")

    detail = (
        db.query(SessionDetail)
        .filter(SessionDetail.session_id == session_id, SessionDetail.order_index == order_index)
        .first()
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi tương ứng")

    # Tạo file tạm trong thư mục temp của hệ thống
    temp_dir = tempfile.gettempdir()
    file_ext = os.path.splitext(video_file.filename)[1] or ".webm"
    temp_filename = f"interview_{session_id}_q{order_index}{file_ext}"
    temp_file_path = os.path.join(temp_dir, temp_filename)

    # Lưu nhanh file nhị phân vào ổ đĩa tạm
    content = await video_file.read()
    with open(temp_file_path, "wb") as f:
        f.write(content)

    # Đánh dấu trạng thái PROCESSING
    detail.status = "PROCESSING"
    db.commit()

    # Bắn tác vụ nền xử lý ngầm (Asynchronous In-process Task)
    background_tasks.add_task(
        process_answer_in_background,
        session_id=session_id,
        order_index=order_index,
        temp_video_path=temp_file_path,
    )

    return AnswerUploadResponse(
        status="PROCESSING",
        message=f"Video câu {order_index} đã được tiếp nhận và đang được AI phân tích ngầm.",
        session_id=session_id,
        order_index=order_index,
    )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Kiểm tra tiến độ xử lý ngầm của các câu hỏi."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên phỏng vấn")

    details = (
        db.query(SessionDetail)
        .filter(SessionDetail.session_id == session_id)
        .order_by(SessionDetail.order_index.asc())
        .all()
    )

    items = [
        QuestionStatusItem(order_index=d.order_index, status=d.status)
        for d in details
    ]
    all_done = all(d.status in ["COMPLETED", "FAILED"] for d in details) if details else False

    return SessionStatusResponse(
        session_id=session_id,
        overall_status=session.status,
        questions=items,
        is_fully_completed=all_done,
    )


@router.get("/{session_id}/results", response_model=SessionResultResponse)
def get_session_results(session_id: str, db: Session = Depends(get_db)):
    """Lấy toàn bộ kết quả phân tích đa phương thức của cả phiên."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên phỏng vấn")

    details = (
        db.query(SessionDetail)
        .filter(SessionDetail.session_id == session_id)
        .order_by(SessionDetail.order_index.asc())
        .all()
    )

    result_details = []
    total_filler = 0
    content_scores = []

    for d in details:
        total_filler += d.filler_words_count or 0
        if d.status == "COMPLETED" and not (d.ai_feedback or {}).get("metadata", {}).get("is_mock", False):
            content_scores.append(d.content_score or 0.0)

        result_details.append(
            QuestionResultDetail(
                order_index=d.order_index,
                question_text=d.question_text,
                transcript=d.transcript or "",
                filler_words_count=d.filler_words_count or 0,
                metrics={
                    "confidence_score": d.confidence_score or 0.0,
                    "stress_score": d.stress_score or 0.0,
                    "content_score": d.content_score or 0.0,
                },
                emotion_timeline=d.emotion_timeline or [],
                ai_feedback=d.ai_feedback or {},
            )
        )

    avg_content = sum(content_scores) / len(content_scores) if content_scores else 0.0

    summary = SessionSummary(
        overall_score=session.overall_score or 0.0,
        content_score_avg=round(avg_content, 1),
        confidence_score_avg=session.confidence_avg or 0.0,
        stress_score_avg=session.stress_avg or 0.0,
        total_filler_words=total_filler,
        final_verdict=(
            "Xem nhận xét AI theo từng câu; điểm tổng chỉ tính các câu đã phân tích thành công."
            if content_scores else "Chưa có câu trả lời được đánh giá thành công."
        ),
    )

    return SessionResultResponse(
        session_id=session.id,
        role_name=session.role_name,
        summary=summary,
        details=result_details,
    )

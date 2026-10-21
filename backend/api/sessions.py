import os
import uuid
import tempfile
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..database import get_db
from ..models import User, InterviewSession, SessionDetail, Question, GeneratedQuestionSet
from ..schemas import (
    SessionStartRequest,
    SessionStartResponse,
    AnswerUploadResponse,
    SessionStatusResponse,
    QuestionStatusItem,
    SessionResultResponse,
    SessionSummary,
    QuestionResultDetail,
    SessionHistoryItem,
    QuestionItem,
)
from .questions import get_questions_for_role
from ..services.pipeline_worker import process_answer_in_background
from ..services.question_contracts import QuestionGenerationResponse, normalized_text

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/history", response_model=List[SessionHistoryItem])
def get_session_history(
    user_id: Optional[str] = Query(None, description="Lọc theo user_id"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách lịch sử tất cả các phiên phỏng vấn đã thực hiện.
    Dùng cho trang HistoryPage và UserHomePage.
    """
    query = db.query(InterviewSession)
    if user_id:
        query = query.filter(InterviewSession.user_id == user_id)
    
    sessions = query.order_by(InterviewSession.created_at.desc()).all()
    results = []

    for s in sessions:
        # Tính toán các chỉ số chi tiết từ các câu hỏi con
        details = db.query(SessionDetail).filter(SessionDetail.session_id == s.id).all()
        total_filler = sum(d.filler_words_count or 0 for d in details)
        
        content_scores = [d.content_score for d in details if d.content_score and d.content_score > 0]
        avg_content = round(sum(content_scores) / len(content_scores), 1) if content_scores else (s.overall_score or 75.0)

        # Stress level
        stress_val = s.stress_avg or 0.0
        if stress_val > 50:
            stress_level = "high"
        elif stress_val > 30:
            stress_level = "medium"
        else:
            stress_level = "low"

        # Voice score ước lượng dựa trên số từ đệm và độ lưu loát
        voice_score = round(max(50.0, 100.0 - (total_filler * 1.5)), 1)
        expression_score = round(s.confidence_avg or 80.0, 1)

        # Feedback tóm tắt
        feedback = ""
        for d in details:
            if d.ai_feedback and isinstance(d.ai_feedback, dict):
                critique = d.ai_feedback.get("content_critique") or d.ai_feedback.get("delivery_critique")
                if critique:
                    feedback = critique[:120] + "..." if len(critique) > 120 else critique
                    break
        if not feedback:
            feedback = f"Phiên phỏng vấn hoàn thành với điểm tổng {s.overall_score or 0}/100."

        results.append(
            SessionHistoryItem(
                session_id=s.id,
                role_name=s.role_name,
                level=s.level or "fresher",
                overall_score=round(s.overall_score or 0.0, 1),
                content_score=avg_content,
                voice_score=voice_score,
                expression_score=expression_score,
                filler_count=total_filler,
                stress_level=stress_level,
                feedback=feedback,
                created_at=s.created_at.isoformat() if s.created_at else datetime.utcnow().isoformat(),
            )
        )

    return results


@router.get("/recent", response_model=List[SessionHistoryItem])
def get_recent_sessions(
    limit: int = Query(3, ge=1, le=20, description="Số lượng phiên gần nhất cần lấy"),
    user_id: Optional[str] = Query(None, description="Lọc theo user_id"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách N phiên phỏng vấn mới nhất hiển thị trên UserHomePage.
    """
    history = get_session_history(user_id=user_id, db=db)
    return history[:limit]


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
def start_interview_session(req: SessionStartRequest, db: Session = Depends(get_db)):
    """
    Khởi tạo phiên phỏng vấn mới:
    - Nếu có generated_set_id: dùng đúng bộ câu hỏi đã sinh và xem trước.
    - Nếu có question_ids: lấy câu hỏi tương ứng trong bảng questions.
    - Nếu không: sinh câu hỏi mặc định theo role_name.
    - Tạo session và session_details.
    """
    questions: List[QuestionItem] = []
    role_name, level, jd_text = req.role_name, req.level or "fresher", req.jd_text
    generated_set = None
    if req.generated_set_id is not None:
        generated_set = db.get(GeneratedQuestionSet, str(req.generated_set_id))
        if generated_set is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy bộ câu hỏi đã sinh; hãy sinh lại.")
        if (normalized_text(req.role_name) != normalized_text(generated_set.role_name)
                or ("level" in req.model_fields_set and req.level is not None and req.level != generated_set.level)
                or (req.jd_text is not None and normalized_text(req.jd_text) != normalized_text(generated_set.jd_text))):
            raise HTTPException(status_code=409, detail="Vị trí, level hoặc JD đã đổi; hãy sinh lại câu hỏi trước khi bắt đầu.")
        try:
            preview = QuestionGenerationResponse(
                generated_set_id=generated_set.id, role_name=generated_set.role_name, level=generated_set.level,
                total=len(generated_set.questions), questions=generated_set.questions,
                metadata=generated_set.generation_metadata, created_at=generated_set.created_at,
            )
        except (ValidationError, TypeError) as exc:
            raise HTTPException(status_code=409, detail="Bộ câu hỏi lưu không hợp lệ; hãy sinh lại.") from exc
        questions = [QuestionItem(order_index=q.order_index, question_text=q.question_text,
                                  time_limit_seconds=q.time_limit_seconds) for q in preview.questions]
        role_name, level, jd_text = generated_set.role_name, generated_set.level, generated_set.jd_text

    user_id = req.user_id or "guest_user"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=f"{user_id}@mockinterview.local", full_name="Ứng viên Thử nghiệm")
        db.add(user)
        db.commit()

    session_id = str(uuid.uuid4())
    session = InterviewSession(
        id=session_id,
        user_id=user.id,
        role_name=role_name,
        level=level,
        jd_text=jd_text,
        status="IN_PROGRESS",
    )
    db.add(session)

    # Sinh hoặc lấy danh sách câu hỏi
    if req.question_ids:
        db_questions = db.query(Question).filter(Question.id.in_(req.question_ids)).all()
        # Duy trì đúng thứ tự của req.question_ids
        q_map = {q.id: q for q in db_questions}
        order = 1
        for q_id in req.question_ids:
            if q_id in q_map:
                q_obj = q_map[q_id]
                questions.append(
                    QuestionItem(
                        order_index=order,
                        question_text=q_obj.question_text,
                        time_limit_seconds=q_obj.time_limit_seconds or 120,
                    )
                )
                order += 1

    # Nếu không tìm thấy theo question_ids, fallback get_questions_for_role
    if not questions:
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
        role_name=role_name,
        level=level,
        total_questions=len(questions),
        questions=questions,
        created_at=datetime.utcnow().isoformat(),
        generated_set_id=generated_set.id if generated_set is not None else None,
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
    - Lưu tạm an toàn vào thư mục tempfile.gettempdir()
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

    # Lưu file tạm an toàn đa nền tảng
    temp_dir = os.path.join(tempfile.gettempdir(), "interview_tmp") if os.name == "nt" else "/tmp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"{session_id}_{order_index}_{uuid.uuid4().hex[:6]}.webm"
    temp_video_path = os.path.join(temp_dir, temp_filename)

    with open(temp_video_path, "wb") as f:
        content = await video_file.read()
        f.write(content)

    detail.status = "PROCESSING"
    db.commit()

    # Kích hoạt background task
    background_tasks.add_task(
        process_answer_in_background,
        session_id=session_id,
        order_index=order_index,
        temp_video_path=temp_video_path,
    )

    return AnswerUploadResponse(
        status="PROCESSING",
        message="Video đã được tải lên thành công, AI đang phân tích đa phương thức.",
        session_id=session_id,
        order_index=order_index,
    )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Kiểm tra tiến độ phân tích các câu hỏi trong phiên."""
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
                video_url=d.video_url,
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

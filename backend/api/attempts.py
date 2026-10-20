from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Attempt, AttemptAnswer
from ..schemas import (
    AttemptFullDetailResponse,
    AttemptSummaryResponse,
    SubmitAnswerRequest,
)

router = APIRouter(
    prefix="/api/user/attempts", tags=["Attempts (Lịch sử làm bài)"]
)


@router.post("/{attempt_id}/submit-answer")
def submit_answer(
    attempt_id: str,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_db),
):
    user_id = "user_123"

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id, Attempt.user_id == user_id)
        .first()
    )
    if not attempt or attempt.status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Lần làm bài không tồn tại hoặc đã chốt kết quả",
        )

    db_correct_answer = "A"
    db_question_max_score = 10.0

    user_ans = payload.user_answer.strip()
    is_correct = user_ans.upper() == db_correct_answer.upper()
    earned_score = db_question_max_score if is_correct else 0.0

    answer_record = (
        db.query(AttemptAnswer)
        .filter(
            AttemptAnswer.attempt_id == attempt_id,
            AttemptAnswer.question_id == payload.question_id,
        )
        .first()
    )

    if not answer_record:
        answer_record = AttemptAnswer(
            attempt_id=attempt_id,
            question_id=payload.question_id,
        )
        db.add(answer_record)

    answer_record.user_answer = user_ans
    answer_record.correct_answer_snapshot = db_correct_answer
    answer_record.is_correct = is_correct
    answer_record.score = earned_score
    answer_record.max_score = db_question_max_score

    db.commit()
    return {"message": "Đã lưu câu trả lời", "is_correct": is_correct}


@router.post("/{attempt_id}/complete")
def complete_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt or attempt.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Không thể chốt bài")

    answers = (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )
    total = sum(answer.score for answer in answers)
    max_score = sum(answer.max_score for answer in answers)

    attempt.total_score = total
    attempt.max_score = max_score
    attempt.completed_at = datetime.utcnow()
    attempt.status = "COMPLETED"

    db.commit()
    return {"message": "Đã nộp bài và chốt điểm", "total_score": total}


@router.get("", response_model=List[AttemptSummaryResponse])
def get_user_attempts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    user_id = "user_123"
    return (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id)
        .order_by(Attempt.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id}", response_model=AttemptFullDetailResponse)
def get_attempt_detail(id: str, db: Session = Depends(get_db)):
    user_id = "user_123"
    attempt = db.query(Attempt).filter(Attempt.id == id).first()

    if not attempt:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy lịch sử làm bài"
        )
    if attempt.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền xem lịch sử của người khác",
        )

    return attempt

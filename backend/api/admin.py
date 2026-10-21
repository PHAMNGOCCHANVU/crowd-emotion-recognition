import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_admin_user
from ..models import (
    Industry,
    Position,
    Segment,
    User,
    InterviewSession,
    Question,
    Attempt,
    AgentConversation,
)
from ..schemas import (
    IndustryCreate,
    IndustryUpdate,
    PositionCreate,
    PositionUpdate,
    QuestionCreateAdmin,
    QuestionUpdateAdmin,
    AdminDashboardStats,
    AdminUserListItem,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin_user)],
)


# ==========================================
# 1. DASHBOARD STATS
# ==========================================

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Tính toán số liệu thực tế từ CSDL cho Dashboard Admin."""
    total_users = db.query(User).filter(User.role == "USER").count()
    total_sessions = db.query(InterviewSession).count()
    completed_sessions_query = db.query(InterviewSession).filter(InterviewSession.status == "COMPLETED")
    completed_count = completed_sessions_query.count()

    completion_rate = round((completed_count / total_sessions * 100), 1) if total_sessions > 0 else 0.0

    completed_sessions = completed_sessions_query.all()
    average_score = (
        round(sum(s.overall_score for s in completed_sessions) / len(completed_sessions), 1)
        if completed_sessions
        else 0.0
    )

    recent_db_sessions = (
        db.query(InterviewSession)
        .order_by(InterviewSession.created_at.desc())
        .limit(5)
        .all()
    )

    recent_sessions = []
    for s in recent_db_sessions:
        candidate_name = s.user.full_name if s.user else "Ẩn danh"
        date_str = s.created_at.strftime("%d/%m/%Y") if s.created_at else ""
        recent_sessions.append(
            {
                "session_id": s.id,
                "role": s.role_name,
                "candidate_name": candidate_name,
                "date": date_str,
                "status": "Hoàn thành" if s.status == "COMPLETED" else "Đang làm",
                "score": round(s.overall_score, 1),
            }
        )

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completion_rate": completion_rate,
        "average_score": average_score,
        "recent_sessions": recent_sessions,
    }


# ==========================================
# 2. INDUSTRIES MANAGEMENT
# ==========================================

@router.get("/industries")
def get_industries(db: Session = Depends(get_db)):
    """Lấy danh sách ngành nghề kèm số lượng vị trí trực thuộc."""
    industries = (
        db.query(Industry)
        .filter(Industry.status != "DELETED")
        .order_by(Industry.name.asc())
        .all()
    )
    result = []
    for ind in industries:
        pos_count = (
            db.query(Position)
            .filter(Position.industry_id == ind.id, Position.status != "DELETED")
            .count()
        )
        result.append(
            {
                "id": ind.id,
                "name": ind.name,
                "code": ind.code,
                "status": ind.status,
                "position_count": pos_count,
            }
        )
    return result


@router.post("/industries", status_code=status.HTTP_201_CREATED)
def create_industry(payload: IndustryCreate, db: Session = Depends(get_db)):
    exist = (
        db.query(Industry)
        .filter((Industry.code == payload.code) | (Industry.name == payload.name))
        .first()
    )
    if exist:
        raise HTTPException(status_code=400, detail="Mã hoặc Tên Ngành đã tồn tại")

    new_ind = Industry(**payload.model_dump())
    db.add(new_ind)
    db.commit()
    db.refresh(new_ind)
    return new_ind


@router.patch("/industries/{id}")
def update_industry(id: str, payload: IndustryUpdate, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == id, Industry.status != "DELETED").first()
    if not industry:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành nghề")

    if payload.name is not None and payload.name.strip():
        industry.name = payload.name.strip()
    if payload.code is not None and payload.code.strip():
        new_code = payload.code.strip()
        exist = db.query(Industry).filter(Industry.code == new_code, Industry.id != id).first()
        if exist:
            raise HTTPException(status_code=400, detail="Mã ngành đã tồn tại")
        industry.code = new_code

    db.commit()
    db.refresh(industry)
    return industry


@router.delete("/industries/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_industry(id: str, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành")

    has_positions = (
        db.query(Position)
        .filter(Position.industry_id == id, Position.status != "DELETED")
        .first()
    )
    if has_positions:
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa: Đang có vị trí trực thuộc ngành này",
        )

    industry.status = "DELETED"
    db.commit()


# ==========================================
# 3. POSITIONS MANAGEMENT
# ==========================================

@router.get("/positions")
def get_positions(db: Session = Depends(get_db)):
    """Lấy danh sách vị trí kèm tên ngành nghề và số lượng câu hỏi."""
    positions = (
        db.query(Position)
        .filter(Position.status != "DELETED")
        .order_by(Position.name.asc())
        .all()
    )
    result = []
    for pos in positions:
        q_count = db.query(Question).filter(Question.position_id == pos.id).count()
        result.append(
            {
                "id": pos.id,
                "industry_id": pos.industry_id,
                "industry_name": pos.industry.name if pos.industry else "Chưa phân loại",
                "name": pos.name,
                "code": pos.code,
                "skills": pos.skills or [],
                "duration": pos.duration,
                "icon": pos.icon,
                "status": pos.status,
                "question_count": q_count,
            }
        )
    return result


@router.post("/positions", status_code=status.HTTP_201_CREATED)
def create_position(payload: PositionCreate, db: Session = Depends(get_db)):
    industry = (
        db.query(Industry)
        .filter(Industry.id == payload.industry_id, Industry.status != "DELETED")
        .first()
    )
    if not industry:
        raise HTTPException(status_code=404, detail="Ngành không tồn tại")

    new_pos = Position(**payload.model_dump())
    db.add(new_pos)
    db.commit()
    db.refresh(new_pos)
    return new_pos


@router.patch("/positions/{id}")
def update_position(id: str, payload: PositionUpdate, db: Session = Depends(get_db)):
    pos = db.query(Position).filter(Position.id == id, Position.status != "DELETED").first()
    if not pos:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí")

    if payload.industry_id is not None:
        ind = db.query(Industry).filter(Industry.id == payload.industry_id, Industry.status != "DELETED").first()
        if not ind:
            raise HTTPException(status_code=404, detail="Ngành nghề không tồn tại")
        pos.industry_id = payload.industry_id

    if payload.name is not None and payload.name.strip():
        pos.name = payload.name.strip()
    if payload.code is not None:
        pos.code = payload.code.strip()
    if payload.skills is not None:
        pos.skills = payload.skills
    if payload.duration is not None:
        pos.duration = payload.duration
    if payload.icon is not None:
        pos.icon = payload.icon

    db.commit()
    db.refresh(pos)
    return pos


@router.delete("/positions/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(id: str, db: Session = Depends(get_db)):
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí")

    has_segments = (
        db.query(Segment)
        .filter(Segment.position_id == id, Segment.status != "DELETED")
        .first()
    )
    if has_segments:
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa: Đang có Phân khúc gắn với vị trí này",
        )

    pos.status = "DELETED"
    db.commit()


# ==========================================
# 4. QUESTION BANK MANAGEMENT
# ==========================================

@router.post("/questions", status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreateAdmin, db: Session = Depends(get_db)):
    """Thêm câu hỏi mới vào ngân hàng câu hỏi."""
    pos = db.query(Position).filter(Position.id == payload.position_id, Position.status != "DELETED").first()
    if not pos:
        raise HTTPException(status_code=404, detail="Vị trí không tồn tại")

    q_id = f"q_admin_{uuid.uuid4().hex[:8]}"
    levels = payload.levels if payload.levels else ([payload.level] if payload.level else ["junior"])

    new_q = Question(
        id=q_id,
        position_id=payload.position_id,
        category=payload.category or "Chuyên môn",
        question_text=payload.question_text,
        time_limit_seconds=payload.time_limit_seconds or 120,
        level=payload.level or "junior",
        levels=levels,
        source="DEFAULT",
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q


@router.patch("/questions/{id}")
def update_question(id: str, payload: QuestionUpdateAdmin, db: Session = Depends(get_db)):
    """Cập nhật câu hỏi trong ngân hàng câu hỏi."""
    q = db.query(Question).filter(Question.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    if payload.category is not None:
        q.category = payload.category
    if payload.question_text is not None and payload.question_text.strip():
        q.question_text = payload.question_text.strip()
    if payload.time_limit_seconds is not None:
        q.time_limit_seconds = payload.time_limit_seconds
    if payload.level is not None:
        q.level = payload.level
    if payload.levels is not None:
        q.levels = payload.levels

    db.commit()
    db.refresh(q)
    return q


@router.delete("/questions/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(id: str, db: Session = Depends(get_db)):
    """Xóa câu hỏi khỏi ngân hàng câu hỏi."""
    q = db.query(Question).filter(Question.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    db.delete(q)
    db.commit()


# ==========================================
# 5. USER MANAGEMENT
# ==========================================

@router.get("/users", response_model=List[AdminUserListItem])
def get_users(search: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Lấy danh sách ứng viên kèm số phiên phỏng vấn và điểm trung bình."""
    query = db.query(User).filter(User.role == "USER")
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    users = query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        sessions = db.query(InterviewSession).filter(InterviewSession.user_id == u.id).all()
        session_count = len(sessions)
        avg_score = (
            round(sum(s.overall_score for s in sessions) / session_count, 1)
            if session_count > 0
            else 0.0
        )
        result.append(
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "phone_number": u.phone_number,
                "role": u.role,
                "session_count": session_count,
                "average_score": avg_score,
                "created_at": u.created_at,
            }
        )
    return result


@router.get("/users/{user_id}/sessions")
def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    """Lấy lịch sử các phiên phỏng vấn của một ứng viên cụ thể."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )

    return [
        {
            "session_id": s.id,
            "role_name": s.role_name,
            "level": s.level or "fresher",
            "overall_score": round(s.overall_score, 1),
            "confidence_score": round(s.confidence_avg, 1),
            "stress_score": round(s.stress_avg, 1),
            "status": s.status,
            "created_at": s.created_at.strftime("%d/%m/%Y %H:%M") if s.created_at else "",
        }
        for s in sessions
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Xóa tài khoản ứng viên và các dữ liệu liên quan."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.role == "ADMIN":
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản Quản trị viên")

    # Xóa an toàn các attempts & conversations nếu có
    db.query(Attempt).filter(Attempt.user_id == user_id).delete(synchronize_session=False)
    db.query(AgentConversation).filter(AgentConversation.user_id == user_id).delete(synchronize_session=False)

    # Xóa các sessions (details tự động cascade)
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == user_id).all()
    for s in sessions:
        db.delete(s)

    db.delete(user)
    db.commit()

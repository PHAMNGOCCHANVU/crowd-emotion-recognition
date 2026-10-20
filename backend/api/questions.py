from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
import backend.models as models
from ..schemas import QuestionItem, PositionItem, QuestionListResponse, QuestionDetailItem

router = APIRouter(prefix="/api/questions", tags=["questions"])

DEFAULT_QUESTIONS = {
    "Software Engineer": [
        "Bạn hãy giới thiệu bản thân và chia sẻ dự án phần mềm ấn tượng nhất bạn từng tham gia?",
        "Khi gặp lỗi nghiêm trọng (critical bug) sát giờ release sản phẩm, bạn xử lý như thế nào?",
        "Theo bạn, sự khác biệt giữa xử lý bất đồng bộ (Asynchronous) và đa luồng (Multithreading) là gì?",
    ],
    "Data Analyst": [
        "Bạn hãy giới thiệu bản thân và kinh nghiệm xử lý tập dữ liệu lớn của bạn?",
        "Làm thế nào để bạn giải thích một insight dữ liệu phức tạp cho các bên kinh doanh (stakeholders)?",
        "Bạn thường sử dụng phương pháp nào để phát hiện và xử lý dữ liệu bị khuyết thiếu (missing data)?",
    ],
    "Sales / Business Development": [
        "Bạn hãy giới thiệu bản thân và thành tích doanh số ấn tượng nhất bạn từng đạt được?",
        "Khi khách hàng từ chối vì chê sản phẩm quá đắt, bạn thuyết phục họ như thế nào?",
        "Làm thế nào để bạn duy trì mối quan hệ lâu dài với khách hàng sau khi đã chốt hợp đồng?",
    ],
    "Marketing": [
        "Bạn hãy giới thiệu bản thân và chiến dịch truyền thông thành công nhất bạn từng lên kế hoạch?",
        "Làm thế nào để bạn đo lường hiệu quả (ROI) của một chiến dịch marketing đa kênh?",
        "Bạn ứng phó ra sao nếu một chiến dịch truyền thông bất ngờ gặp phải khủng hoảng dư luận?",
    ],
    "Human Resources (HR)": [
        "Bạn hãy giới thiệu bản thân và phong cách quản trị nhân sự của bạn?",
        "Làm thế nào để bạn giải quyết một bất đồng gay gắt giữa hai trưởng phòng ban?",
        "Bạn có chiến lược gì để giữ chân nhân tài và xây dựng văn hóa doanh nghiệp tích cực?",
    ],
}


def get_questions_for_role(role_name: str, jd_text: str = None) -> List[QuestionItem]:
    """Lấy danh sách 3 câu hỏi phù hợp theo ngành hoặc JD (tương thích ngược)."""
    questions = DEFAULT_QUESTIONS.get(role_name, DEFAULT_QUESTIONS["Software Engineer"])
    return [
        QuestionItem(order_index=i + 1, question_text=q, time_limit_seconds=120)
        for i, q in enumerate(questions)
    ]


@router.get("/roles", response_model=List[str])
def list_available_roles():
    """Lấy danh sách các vị trí phỏng vấn có sẵn (tương thích ngược)."""
    return list(DEFAULT_QUESTIONS.keys())


@router.get("/positions", response_model=List[PositionItem])
def list_positions(
    level: Optional[str] = Query(None, description="Lọc theo level: intern, fresher, junior, mid, senior"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách các vị trí ứng tuyển cho UserHomePage và SetupPage.
    Hỗ trợ lọc theo cấp độ (level).
    """
    positions = db.query(models.Position).filter(models.Position.status == "ACTIVE").all()
    results = []

    for pos in positions:
        industry_name = pos.industry.name if pos.industry else "Công nghệ thông tin"
        
        # Lấy danh sách level của các câu hỏi thuộc vị trí này
        questions = db.query(models.Question).filter(models.Question.position_id == pos.id).all()
        levels_set = set()
        for q in questions:
            if q.levels:
                levels_set.update(q.levels)
            elif q.level:
                levels_set.add(q.level)
        
        available_levels = sorted(list(levels_set)) if levels_set else ["intern", "fresher", "junior", "mid", "senior"]

        if level and level not in available_levels:
            continue

        results.append(
            PositionItem(
                id=pos.id,
                title=pos.name,
                field=industry_name,
                skills=pos.skills or [],
                duration=pos.duration or "3–6 tháng",
                icon=pos.icon or "server",
                levels=available_levels,
            )
        )

    return results


@router.get("", response_model=QuestionListResponse)
def list_questions(
    position_id: str = Query(..., description="Mã vị trí (VD: backend, frontend)"),
    level: Optional[str] = Query(None, description="Cấp độ lọc câu hỏi"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách ngân hàng câu hỏi để ứng viên xem trước tại SetupPage.
    """
    query = db.query(models.Question).filter(models.Question.position_id == position_id)
    all_qs = query.all()

    matched_qs = []
    for q in all_qs:
        if level:
            if q.levels and level in q.levels:
                matched_qs.append(q)
            elif q.level == level:
                matched_qs.append(q)
        else:
            matched_qs.append(q)

    # Nếu không có câu hỏi nào trong DB theo filter, fallback câu hỏi mặc định
    if not matched_qs:
        matched_qs = all_qs[:4] if all_qs else []

    question_items = [
        QuestionDetailItem(
            id=q.id,
            category=q.category or "Chuyên môn",
            question_text=q.question_text,
            time_limit_seconds=q.time_limit_seconds or 120,
        )
        for q in matched_qs
    ]

    return QuestionListResponse(
        position_id=position_id,
        level=level or "all",
        total=len(question_items),
        questions=question_items,
    )

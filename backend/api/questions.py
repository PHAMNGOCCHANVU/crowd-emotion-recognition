import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
import backend.models as models
from ..schemas import (
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    PositionItem,
    QuestionDetailItem,
    QuestionItem,
    QuestionListResponse,
)

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


def _generate_offline_questions_from_jd(
    position_name: str, level: str, jd_text: str
) -> List[dict]:
    """Sinh câu hỏi dự phòng từ JD dựa trên phân tích từ khóa khi không có LLM."""
    common_tech_keywords = [
        "python", "fastapi", "django", "flask", "nodejs", "javascript", "typescript",
        "react", "vue", "angular", "sql", "postgresql", "mysql", "mongodb", "redis",
        "docker", "kubernetes", "aws", "git", "ci/cd", "restful", "graphql", "microservices",
        "machine learning", "deep learning", "nlp", "llm", "pandas", "tableau", "power bi",
        "agile", "scrum", "jira", "figma", "excel", "seo", "kpi",
    ]
    jd_lower = jd_text.lower()
    found_keywords = [kw.capitalize() for kw in common_tech_keywords if kw in jd_lower]

    skill1 = found_keywords[0] if len(found_keywords) > 0 else f"kỹ năng chuyên môn của {position_name}"
    skill2 = found_keywords[1] if len(found_keywords) > 1 else "quy trình làm việc và tối ưu hóa hệ thống"

    return [
        {
            "category": "Chuyên môn (JD)",
            "question_text": f"Dựa trên yêu cầu trong JD về {skill1}, bạn hãy chia sẻ kinh nghiệm triển khai thực tế và cách bạn xử lý khó khăn kỹ thuật khi làm việc với công nghệ này ở mức độ {level}?",
        },
        {
            "category": "Chuyên môn (JD)",
            "question_text": f"Trong bản mô tả công việc có nhấn mạnh đến {skill2}. Bạn đã từng áp dụng kỹ năng này để giải quyết vấn đề hiệu năng hoặc chất lượng sản phẩm như thế nào?",
        },
        {
            "category": "Tình huống (JD)",
            "question_text": f"Với vai trò {position_name} ({level}), khi nhận một yêu cầu khẩn cấp từ JD mà thời hạn gấp hoặc tài liệu chưa rõ ràng, bạn sẽ ưu tiên và phối hợp giải quyết ra sao?",
        },
    ]


@router.get("", response_model=QuestionListResponse)
def list_questions(
    position_id: str = Query(..., description="Mã vị trí (VD: backend, frontend)"),
    level: Optional[str] = Query(None, description="Cấp độ lọc câu hỏi"),
    source: Optional[str] = Query(None, description="Nguồn câu hỏi: DEFAULT hoặc Q-JD (bỏ trống hoặc all để lấy tất cả)"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách ngân hàng câu hỏi để ứng viên xem trước tại SetupPage và PracticePage.
    Hỗ trợ lọc theo vị trí, level và nguồn gốc (DEFAULT hoặc Q-JD).
    """
    query = db.query(models.Question).filter(models.Question.position_id == position_id)

    if source and source.strip().lower() != "all":
        query = query.filter(models.Question.source == source.strip())

    all_qs = query.order_by(models.Question.created_at.desc(), models.Question.id.asc()).all()

    matched_qs = []
    for q in all_qs:
        if level and level.strip().lower() != "all":
            lvl_clean = level.strip().lower()
            if q.levels and lvl_clean in [l.lower() for l in q.levels]:
                matched_qs.append(q)
            elif q.level and q.level.lower() == lvl_clean:
                matched_qs.append(q)
        else:
            matched_qs.append(q)

    # Chỉ fallback câu hỏi mặc định khi không chỉ định nguồn lọc đặc thù hoặc nguồn là DEFAULT
    if not matched_qs and (not source or source.strip().upper() == "DEFAULT"):
        matched_qs = all_qs[:4] if all_qs else []

    question_items = [
        QuestionDetailItem(
            id=q.id,
            category=q.category or "Chuyên môn",
            question_text=q.question_text,
            time_limit_seconds=q.time_limit_seconds or 120,
            level=q.level or level or "junior",
            source=q.source or "DEFAULT",
            created_at=q.created_at.isoformat() if q.created_at else None,
        )
        for q in matched_qs
    ]

    return QuestionListResponse(
        position_id=position_id,
        level=level or "all",
        total=len(question_items),
        questions=question_items,
    )


@router.post(
    "/generate-from-jd",
    response_model=GenerateQuestionsResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_questions_from_jd(
    payload: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
):
    """
    Sinh câu hỏi phỏng vấn tự động từ Job Description bằng AI (Gemini Flash hoặc Offline Fallback)
    và lưu trực tiếp vào CSDL với source='Q-JD'.
    """
    # 1. Kiểm tra position_id
    pos = db.query(models.Position).filter(models.Position.id == payload.position_id).first()
    if not pos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy vị trí tuyển dụng với position_id được cung cấp.",
        )

    # 2. Kiểm tra level
    valid_levels = ["intern", "fresher", "junior", "mid", "senior"]
    if payload.level.lower() not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Level không hợp lệ. Phải thuộc một trong các cấp: {', '.join(valid_levels)}.",
        )

    # 3. Kiểm tra jd_text
    jd_clean = payload.jd_text.strip()
    if len(jd_clean) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mô tả công việc (JD) phải có tối thiểu 20 ký tự.",
        )

    # 4. Sinh câu hỏi từ JD (Ưu tiên Gemini Flash, Fallback sang Offline generator)
    raw_questions: List[dict] = []
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            prompt = (
                f"Bạn là chuyên gia phỏng vấn nhân sự kỹ thuật.\n"
                f"Dựa vào Mô tả công việc (JD) sau cho vị trí '{pos.name}' ở cấp độ '{payload.level}', "
                f"hãy sinh ra đúng 3 câu hỏi phỏng vấn thực tế và bám sát JD nhất:\n"
                f"- 2 câu hỏi kỹ thuật/chuyên môn kiểm tra kiến thức nêu trong JD.\n"
                f"- 1 câu hỏi tình huống giải quyết vấn đề thực tế trong môi trường dự án.\n\n"
                f"JD:\n\"\"\"\n{jd_clean}\n\"\"\"\n\n"
                f"Hãy trả về JSON thuần túy (không kèm markdown ngoài) theo cấu trúc mảng danh sách:\n"
                f'[\n  {{"category": "Chuyên môn (JD)", "question_text": "..."}},\n'
                f'  {{"category": "Chuyên môn (JD)", "question_text": "..."}},\n'
                f'  {{"category": "Tình huống (JD)", "question_text": "..."}}\n]'
            )
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
            if resp and resp.text:
                parsed = json.loads(resp.text)
                if isinstance(parsed, list) and len(parsed) >= 1:
                    raw_questions = parsed
        except Exception as e:
            print(f"⚠️ Không thể gọi Gemini trực tiếp, sử dụng bộ sinh Offline Fallback: {e}")

    if not raw_questions:
        raw_questions = _generate_offline_questions_from_jd(
            position_name=pos.name, level=payload.level, jd_text=jd_clean
        )

    # 5. Lưu câu hỏi vào CSDL
    created_questions: List[models.Question] = []
    for item in raw_questions[:4]:
        q_text = item.get("question_text", "").strip()
        if not q_text:
            continue
        q_cat = item.get("category", "Chuyên môn (JD)")
        new_q = models.Question(
            id=f"qjd_{uuid.uuid4().hex[:8]}",
            position_id=pos.id,
            category=q_cat,
            question_text=q_text,
            time_limit_seconds=120,
            level=payload.level.lower(),
            levels=[payload.level.lower()],
            source="Q-JD",
            created_at=datetime.utcnow(),
        )
        db.add(new_q)
        created_questions.append(new_q)

    db.commit()

    # 6. Chuẩn bị kết quả trả về
    res_items = [
        QuestionDetailItem(
            id=q.id,
            category=q.category or "Chuyên môn (JD)",
            question_text=q.question_text,
            time_limit_seconds=q.time_limit_seconds or 120,
            level=q.level,
            source=q.source,
            created_at=q.created_at.isoformat() if q.created_at else None,
        )
        for q in created_questions
    ]

    return GenerateQuestionsResponse(
        status="success",
        message=f"Đã sinh thành công {len(res_items)} câu hỏi từ JD và lưu vào ngân hàng câu hỏi.",
        generated_count=len(res_items),
        questions=res_items,
    )

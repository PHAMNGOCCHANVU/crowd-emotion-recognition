from typing import List
from fastapi import APIRouter
from ..schemas import QuestionItem

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
    """Lấy danh sách 3 câu hỏi phù hợp theo ngành hoặc JD."""
    questions = DEFAULT_QUESTIONS.get(role_name, DEFAULT_QUESTIONS["Software Engineer"])
    return [
        QuestionItem(order_index=i + 1, question_text=q, time_limit_seconds=120)
        for i, q in enumerate(questions)
    ]


@router.get("/roles", response_model=List[str])
def list_available_roles():
    """Lấy danh sách các vị trí phỏng vấn có sẵn."""
    return list(DEFAULT_QUESTIONS.keys())

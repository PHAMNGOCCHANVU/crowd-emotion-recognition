from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ==========================================
# CÁC SCHEMAS PHỤC VỤ PHỎNG VẤN CỐT LÕI (CORE INTERVIEW)
# ==========================================

class QuestionItem(BaseModel):
    order_index: int
    question_text: str
    time_limit_seconds: int = 120


class SessionStartRequest(BaseModel):
    user_id: str | None = "guest_user"
    role_name: str = Field(..., description="Vị trí ứng tuyển (Software Engineer, Sales, HR, etc.)")
    jd_text: str | None = None
    level: str | None = Field("fresher", description="Cấp độ: intern, fresher, junior, mid, senior")
    question_ids: list[str] | None = Field(None, description="Danh sách ID câu hỏi chọn trước")


class SessionStartResponse(BaseModel):
    session_id: str
    role_name: str
    level: str | None = "fresher"
    total_questions: int
    questions: list[QuestionItem]
    created_at: str


class AnswerUploadResponse(BaseModel):
    status: str = "PROCESSING"
    message: str
    session_id: str
    order_index: int


class QuestionStatusItem(BaseModel):
    order_index: int
    status: str


class SessionStatusResponse(BaseModel):
    session_id: str
    overall_status: str
    questions: list[QuestionStatusItem]
    is_fully_completed: bool


class QuestionResultDetail(BaseModel):
    order_index: int
    question_text: str
    transcript: str | None = ""
    filler_words_count: int = 0
    metrics: dict[str, float]
    emotion_timeline: list[dict[str, Any]] = []
    ai_feedback: dict[str, Any] = {}
    video_url: str | None = None


class SessionSummary(BaseModel):
    overall_score: float
    content_score_avg: float
    confidence_score_avg: float
    stress_score_avg: float
    total_filler_words: int
    final_verdict: str


class SessionResultResponse(BaseModel):
    session_id: str
    role_name: str
    summary: SessionSummary
    details: list[QuestionResultDetail]


class ChatRequest(BaseModel):
    message: str = Field(..., description="Nội dung câu hỏi của ứng viên gửi cho AI Coach")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: list[str] = []
    is_mock: bool = False
    timestamp: str


# ==========================================
# CÁC SCHEMAS PHỤC VỤ DASHBOARD, LỊCH SỬ & POSITIONS
# ==========================================

class SessionHistoryItem(BaseModel):
    session_id: str
    role_name: str
    level: str | None = "fresher"
    overall_score: float
    content_score: float = 0.0
    voice_score: float = 0.0
    expression_score: float = 0.0
    filler_count: int = 0
    stress_level: str = "low"
    feedback: str | None = ""
    created_at: str

    class Config:
        from_attributes = True


class PositionItem(BaseModel):
    id: str
    title: str
    field: str
    skills: list[str] = []
    duration: str = "3–6 tháng"
    icon: str = "server"
    levels: list[str] = ["intern", "fresher", "junior", "mid", "senior"]


class QuestionDetailItem(BaseModel):
    id: str
    category: str
    question_text: str
    time_limit_seconds: int = 120
    level: str | None = "junior"
    source: str = "DEFAULT"
    created_at: str | None = None


class QuestionListResponse(BaseModel):
    position_id: str
    level: str
    total: int
    questions: list[QuestionDetailItem]


class GenerateQuestionsRequest(BaseModel):
    position_id: str = Field(..., description="Mã vị trí (VD: backend, frontend)")
    level: str = Field(..., description="Cấp độ: intern, fresher, junior, mid, senior")
    jd_text: str = Field(..., min_length=15, max_length=150000, description="Mô tả công việc tối đa 10.000 từ")


class GenerateQuestionsResponse(BaseModel):
    status: str = "success"
    message: str
    generated_count: int
    questions: list[QuestionDetailItem]


# ==========================================
# CÁC SCHEMAS CHO AI ADVISOR (AGENT)
# ==========================================

class AgentMessageItem(BaseModel):
    role: str = Field(..., description="user hoặc agent")
    content: str


class AgentChatRequest(BaseModel):
    conversation_id: str | None = None
    session_id: str | None = Field(None, description="Mã phiên phỏng vấn cụ thể (nếu đang phân tích trong một phiên)")
    message: str = Field(..., description="Nội dung câu hỏi gửi AI Advisor")
    history: list[AgentMessageItem] | None = []


class AgentChatResponse(BaseModel):
    reply: str
    suggestions: list[str] = []
    conversation_id: str | None = None
    tools_used: list[str] = []


class AgentConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[AgentMessageItem] = []

    class Config:
        from_attributes = True


# ==========================================
# CÁC SCHEMAS TỪ BRANCH BACKEND-API (SEGMENTS, ATTEMPTS, USERS, ADMIN)
# ==========================================

class SegmentBase(BaseModel):
    name: str = Field(..., description="Tên phân khúc")
    code: str | None = Field(None, description="Mã định danh")
    description: str | None = None
    industry_id: str
    position_id: str
    status: str | None = "ACTIVE"
    sort_order: int | None = 0


class SegmentCreate(SegmentBase):
    pass


class SegmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    industry_id: str | None = None
    position_id: str | None = None
    status: str | None = None
    sort_order: int | None = None


class SegmentResponse(SegmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmitAnswerRequest(BaseModel):
    question_id: str
    user_answer: str


class AttemptSummaryResponse(BaseModel):
    id: str
    test_id: str
    started_at: datetime
    completed_at: datetime | None
    total_score: float
    max_score: float
    status: str

    class Config:
        from_attributes = True


class AttemptAnswerDetail(BaseModel):
    question_id: str
    user_answer: str | None
    correct_answer_snapshot: str | None
    is_correct: bool | None
    score: float
    max_score: float


class AttemptSectionDetail(BaseModel):
    section_id: str
    score: float
    max_score: float
    correct_count: int
    question_count: int


class AttemptFullDetailResponse(AttemptSummaryResponse):
    sections: list[AttemptSectionDetail]
    answers: list[AttemptAnswerDetail]


class IndustryCreate(BaseModel):
    name: str
    code: str


class PositionCreate(BaseModel):
    industry_id: str
    name: str
    code: str | None = None
    skills: list[str] | None = None
    duration: str | None = "3–6 tháng"
    icon: str | None = "server"


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: str | None
    role: str

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(
        None, min_length=2, description="Họ và tên"
    )
    phone_number: str | None = Field(None, description="Số điện thoại")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(
        ..., min_length=8, description="Mật khẩu mới tối thiểu 8 ký tự"
    )


# ==========================================
# CÁC SCHEMAS PHỤC VỤ ADMIN MANAGEMENT
# ==========================================

class AdminRecentSessionItem(BaseModel):
    session_id: str
    role: str
    candidate_name: str
    date: str
    status: str
    score: float


class AdminDashboardStats(BaseModel):
    total_users: int
    total_sessions: int
    completion_rate: float
    average_score: float
    recent_sessions: list[AdminRecentSessionItem] = []


class AdminUserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: str | None = None
    role: str
    session_count: int = 0
    average_score: float = 0.0
    created_at: datetime | None = None


class IndustryUpdate(BaseModel):
    name: str | None = None
    code: str | None = None


class PositionUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    industry_id: str | None = None
    skills: list[str] | None = None
    duration: str | None = None
    icon: str | None = None


class QuestionCreateAdmin(BaseModel):
    position_id: str
    category: str | None = "Chuyên môn"
    question_text: str
    time_limit_seconds: int | None = 120
    level: str | None = "junior"
    levels: list[str] | None = None


class QuestionUpdateAdmin(BaseModel):
    category: str | None = None
    question_text: str | None = None
    time_limit_seconds: int | None = None
    level: str | None = None
    levels: list[str] | None = None


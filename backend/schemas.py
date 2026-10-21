from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==========================================
# CÁC SCHEMAS PHỤC VỤ PHỎNG VẤN CỐT LÕI (CORE INTERVIEW)
# ==========================================

class QuestionItem(BaseModel):
    order_index: int
    question_text: str
    time_limit_seconds: int = 120


class SessionStartRequest(BaseModel):
    user_id: Optional[str] = "guest_user"
    role_name: str = Field(..., description="Vị trí ứng tuyển (Software Engineer, Sales, HR, etc.)")
    jd_text: Optional[str] = None
    level: Optional[str] = Field("fresher", description="Cấp độ: intern, fresher, junior, mid, senior")
    question_ids: Optional[List[str]] = Field(None, description="Danh sách ID câu hỏi chọn trước")


class SessionStartResponse(BaseModel):
    session_id: str
    role_name: str
    level: Optional[str] = "fresher"
    total_questions: int
    questions: List[QuestionItem]
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
    questions: List[QuestionStatusItem]
    is_fully_completed: bool


class QuestionResultDetail(BaseModel):
    order_index: int
    question_text: str
    transcript: Optional[str] = ""
    filler_words_count: int = 0
    metrics: Dict[str, float]
    emotion_timeline: List[Dict[str, Any]] = []
    ai_feedback: Dict[str, Any] = {}
    video_url: Optional[str] = None


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
    details: List[QuestionResultDetail]


class ChatRequest(BaseModel):
    message: str = Field(..., description="Nội dung câu hỏi của ứng viên gửi cho AI Coach")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: List[str] = []
    is_mock: bool = False
    timestamp: str


# ==========================================
# CÁC SCHEMAS PHỤC VỤ DASHBOARD, LỊCH SỬ & POSITIONS
# ==========================================

class SessionHistoryItem(BaseModel):
    session_id: str
    role_name: str
    level: Optional[str] = "fresher"
    overall_score: float
    content_score: float = 0.0
    voice_score: float = 0.0
    expression_score: float = 0.0
    filler_count: int = 0
    stress_level: str = "low"
    feedback: Optional[str] = ""
    created_at: str

    class Config:
        from_attributes = True


class PositionItem(BaseModel):
    id: str
    title: str
    field: str
    skills: List[str] = []
    duration: str = "3–6 tháng"
    icon: str = "server"
    levels: List[str] = ["intern", "fresher", "junior", "mid", "senior"]


class QuestionDetailItem(BaseModel):
    id: str
    category: str
    question_text: str
    time_limit_seconds: int = 120
    level: Optional[str] = "junior"
    source: str = "DEFAULT"
    created_at: Optional[str] = None


class QuestionListResponse(BaseModel):
    position_id: str
    level: str
    total: int
    questions: List[QuestionDetailItem]


class GenerateQuestionsRequest(BaseModel):
    position_id: str = Field(..., description="Mã vị trí (VD: backend, frontend)")
    level: str = Field(..., description="Cấp độ: intern, fresher, junior, mid, senior")
    jd_text: str = Field(..., min_length=20, max_length=10000, description="Mô tả công việc tối thiểu 20 ký tự")


class GenerateQuestionsResponse(BaseModel):
    status: str = "success"
    message: str
    generated_count: int
    questions: List[QuestionDetailItem]


# ==========================================
# CÁC SCHEMAS CHO AI ADVISOR (AGENT)
# ==========================================

class AgentMessageItem(BaseModel):
    role: str = Field(..., description="user hoặc agent")
    content: str


class AgentChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., description="Nội dung câu hỏi gửi AI Advisor")
    history: Optional[List[AgentMessageItem]] = []


class AgentChatResponse(BaseModel):
    reply: str
    suggestions: List[str] = []
    conversation_id: Optional[str] = None


class AgentConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AgentMessageItem] = []

    class Config:
        from_attributes = True


# ==========================================
# CÁC SCHEMAS TỪ BRANCH BACKEND-API (SEGMENTS, ATTEMPTS, USERS, ADMIN)
# ==========================================

class SegmentBase(BaseModel):
    name: str = Field(..., description="Tên phân khúc")
    code: Optional[str] = Field(None, description="Mã định danh")
    description: Optional[str] = None
    industry_id: str
    position_id: str
    status: Optional[str] = "ACTIVE"
    sort_order: Optional[int] = 0


class SegmentCreate(SegmentBase):
    pass


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    industry_id: Optional[str] = None
    position_id: Optional[str] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


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
    completed_at: Optional[datetime]
    total_score: float
    max_score: float
    status: str

    class Config:
        from_attributes = True


class AttemptAnswerDetail(BaseModel):
    question_id: str
    user_answer: Optional[str]
    correct_answer_snapshot: Optional[str]
    is_correct: Optional[bool]
    score: float
    max_score: float


class AttemptSectionDetail(BaseModel):
    section_id: str
    score: float
    max_score: float
    correct_count: int
    question_count: int


class AttemptFullDetailResponse(AttemptSummaryResponse):
    sections: List[AttemptSectionDetail]
    answers: List[AttemptAnswerDetail]


class IndustryCreate(BaseModel):
    name: str
    code: str


class PositionCreate(BaseModel):
    industry_id: str
    name: str
    code: Optional[str] = None
    skills: Optional[List[str]] = None
    duration: Optional[str] = "3–6 tháng"
    icon: Optional[str] = "server"


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    role: str

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(
        None, min_length=2, description="Họ và tên"
    )
    phone_number: Optional[str] = Field(None, description="Số điện thoại")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(
        ..., min_length=8, description="Mật khẩu mới tối thiểu 8 ký tự"
    )

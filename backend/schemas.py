from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    order_index: int
    question_text: str
    time_limit_seconds: int = 120


class SessionStartRequest(BaseModel):
    user_id: Optional[str] = "guest_user"
    role_name: str = Field(..., description="Vị trí ứng tuyển (Software Engineer, Sales, HR, etc.)")
    jd_text: Optional[str] = None


class SessionStartResponse(BaseModel):
    session_id: str
    role_name: str
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

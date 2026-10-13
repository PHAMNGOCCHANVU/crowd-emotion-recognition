from typing import List, Optional, Dict, Any
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


class ChatRequest(BaseModel):
    message: str = Field(..., description="Nội dung câu hỏi của ứng viên gửi cho AI Coach")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: List[str] = []
    is_mock: bool = False
    timestamp: str


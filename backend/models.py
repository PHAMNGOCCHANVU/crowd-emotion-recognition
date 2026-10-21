import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(20), default="USER")
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="user")
    attempts = relationship("Attempt", back_populates="user")
    conversations = relationship("AgentConversation", back_populates="user")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    role_name = Column(String(100), nullable=False)
    level = Column(String(50), default="junior", nullable=True)
    jd_text = Column(Text, nullable=True)
    overall_score = Column(Float, default=0.0)
    confidence_avg = Column(Float, default=0.0)
    stress_avg = Column(Float, default=0.0)
    status = Column(String(20), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    details = relationship("SessionDetail", back_populates="session", cascade="all, delete-orphan")


class SessionDetail(Base):
    __tablename__ = "session_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    
    transcript = Column(Text, nullable=True)
    filler_words_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    stress_score = Column(Float, default=0.0)
    content_score = Column(Float, default=0.0)
    
    emotion_timeline = Column(JSON, nullable=True)  # [{"second": 1, "emotion": "Normal", ...}]
    ai_feedback = Column(JSON, nullable=True)       # {"content_critique", "delivery_critique", "suggested_answer"}
    video_url = Column(String(500), nullable=True)   # Đường dẫn phát video trực tiếp (Firebase Cloud Storage)
    status = Column(String(20), default="PENDING")   # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="details")


class Industry(Base):
    __tablename__ = "industries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="ACTIVE")

    positions = relationship("Position", back_populates="industry")
    segments = relationship("Segment", back_populates="industry")


class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    industry_id = Column(String(36), ForeignKey("industries.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    skills = Column(JSON, nullable=True)
    duration = Column(String(50), default="3–6 tháng")
    icon = Column(String(50), default="server")
    status = Column(String(20), default="ACTIVE")

    industry = relationship("Industry", back_populates="positions")
    segments = relationship("Segment", back_populates="position")
    questions = relationship("Question", back_populates="position")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)

    industry_id = Column(String(36), ForeignKey("industries.id"), nullable=False)
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=False)

    status = Column(String(20), default="ACTIVE")
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    industry = relationship("Industry", back_populates="segments")
    position = relationship("Position", back_populates="segments")


class Test(Base):
    __tablename__ = "tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship("Section", back_populates="test")
    attempts = relationship("Attempt", back_populates="test")


class Section(Base):
    __tablename__ = "sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey("tests.id"), nullable=True)
    name = Column(String(255), nullable=False)
    sort_order = Column(Integer, default=0)

    test = relationship("Test", back_populates="sections")
    questions = relationship("Question", back_populates="section")
    attempt_section_scores = relationship("AttemptSectionScore", back_populates="section")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(50), primary_key=True)
    section_id = Column(String(36), ForeignKey("sections.id"), nullable=True)
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=True)
    category = Column(String(50), nullable=True)  # Hành vi, Chuyên môn, Tình huống, v.v.
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=True)
    time_limit_seconds = Column(Integer, default=120)
    level = Column(String(50), default="junior")  # intern, fresher, junior, mid, senior
    levels = Column(JSON, nullable=True)          # ["intern", "fresher", "junior", ...]

    source = Column(String(20), default="DEFAULT", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="questions")
    position = relationship("Position", back_populates="questions")
    answers = relationship("AttemptAnswer", back_populates="question")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    test_id = Column(String(36), ForeignKey("tests.id"), nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    status = Column(String(20), default="IN_PROGRESS")

    user = relationship("User", back_populates="attempts")
    test = relationship("Test", back_populates="attempts")
    answers = relationship(
        "AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )
    sections = relationship(
        "AttemptSectionScore", back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(36), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(String(50), ForeignKey("questions.id"), nullable=False)

    user_answer = Column(Text, nullable=True)
    correct_answer_snapshot = Column(Text, nullable=True)

    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)

    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class AttemptSectionScore(Base):
    __tablename__ = "attempt_section_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(36), ForeignKey("attempts.id"), nullable=False)
    section_id = Column(String(36), ForeignKey("sections.id"), nullable=False)

    score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    correct_count = Column(Integer, default=0)
    question_count = Column(Integer, default=0)

    attempt = relationship("Attempt", back_populates="sections")
    section = relationship("Section", back_populates="attempt_section_scores")


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(String(50), primary_key=True, default=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    title = Column(String(255), default="Cuộc trò chuyện mới")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("AgentMessage", back_populates="conversation", cascade="all, delete-orphan")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(String(50), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id = Column(String(50), ForeignKey("agent_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, agent
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("AgentConversation", back_populates="messages")

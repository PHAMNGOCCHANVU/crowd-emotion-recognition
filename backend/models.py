import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="user")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    role_name = Column(String(100), nullable=False)
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

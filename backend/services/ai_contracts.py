"""Member B's service contracts; independent of the API/DB schemas owned by C."""

import os
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class ServiceError(RuntimeError):
    """A safe error code for the background worker (no provider secrets/body)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class AISettings(Contract):
    mode: Literal["live", "mock"] = "live"
    groq_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    gemini_model: str = Field(default="gemini-3.8-flash", min_length=1)
    allow_fallback: bool = True
    timeout_seconds: float = Field(default=20, gt=0, le=120)
    extraction_timeout_seconds: float = Field(default=30, gt=0, le=120)
    max_duration_seconds: float = Field(default=125, gt=0, le=600)
    ffmpeg_binary: str | None = None

    @classmethod
    def from_env(cls) -> Self:
        # The application entry point loads .env; imports have no side effects.
        return cls(
            mode=os.getenv("AI_MODE", "live"),
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            allow_fallback=os.getenv("AI_ALLOW_FALLBACK", "true"),
            timeout_seconds=os.getenv("AI_TIMEOUT_SECONDS", "20"),
            ffmpeg_binary=os.getenv("FFMPEG_BINARY") or None,
        )


class ServiceMetadata(Contract):
    provider: Literal["groq", "gemini", "mock", "local"]
    model: str | None = None
    is_mock: bool = False
    fallback_reason: str | None = None
    latency_ms: float = Field(ge=0)


class WordTimestamp(Contract):
    word: str = Field(min_length=1)
    start: float = Field(ge=0, strict=True)
    end: float = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end < self.start:
            raise ValueError("word end must be >= start")
        return self


class SpeechResult(Contract):
    transcript: str
    language: str | None = None
    words: list[WordTimestamp]
    duration_seconds: float = Field(ge=0)
    filler_words_count: int = Field(ge=0)
    filler_words: dict[str, int]
    metadata: ServiceMetadata


Score = Annotated[float, Field(ge=0, le=100, strict=True)]


class EmotionPoint(Contract):
    second: float = Field(ge=0)
    emotion: Literal["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    is_stress: bool | None = None


class EmotionMetrics(Contract):
    # Missing FER data is not silently converted to zero confidence/stress.
    confidence_score: Score | None = None
    stress_score: Score | None = None
    dominant_emotion: Literal["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"] | None = None
    emotion_distribution: dict[str, float] = Field(default_factory=dict)
    emotion_timeline: list[EmotionPoint] = Field(default_factory=list, max_length=600)


class EvaluationInput(Contract):
    question_text: str = Field(min_length=1, max_length=10000)
    role_name: str = Field(min_length=1, max_length=200)
    transcript: str = Field(max_length=30000)
    filler_words_count: int = Field(ge=0, strict=True)
    emotion_metrics: EmotionMetrics


class InterviewFeedback(Contract):
    content_score: Score
    content_critique: str = Field(min_length=1, max_length=6000)
    delivery_critique: str = Field(min_length=1, max_length=6000)
    suggested_answer: str = Field(min_length=1, max_length=10000)


class EvaluationResult(InterviewFeedback):
    metadata: ServiceMetadata

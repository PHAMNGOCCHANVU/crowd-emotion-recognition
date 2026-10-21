"""Contracts for JD-based question generation, separate from answer scoring."""

import re
import unicodedata
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from .ai_contracts import Contract, ServiceMetadata

InterviewLevel = Literal["intern", "fresher", "junior", "mid", "senior"]


def normalized_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


class QuestionGenerationRequest(Contract):
    role_name: str = Field(min_length=1, max_length=100)
    level: InterviewLevel
    jd_text: str = Field(min_length=20, max_length=20000)
    question_count: Literal[3, 4] = 4


class GeneratedQuestion(Contract):
    category: Literal["Chuyên môn", "Tình huống", "Hành vi"]
    question_text: str = Field(min_length=15, max_length=1500)
    jd_evidence: str = Field(
        min_length=5, max_length=1000,
        description="Trích nguyên văn một yêu cầu hoặc nhiệm vụ trong JD làm căn cứ cho câu hỏi.",
    )


class GeneratedQuestionContent(Contract):
    questions: list[GeneratedQuestion] = Field(min_length=3, max_length=4)

    @model_validator(mode="after")
    def distinct_questions(self):
        keys = [re.sub(r"[^\w]+", " ", normalized_text(q.question_text)).strip()
                for q in self.questions]
        if len(set(keys)) != len(keys):
            raise ValueError("Questions must be distinct")
        return self


class GeneratedQuestionItem(GeneratedQuestion):
    id: str
    order_index: int = Field(ge=1, le=4)
    time_limit_seconds: Literal[120] = 120


class QuestionGenerationResponse(Contract):
    generated_set_id: str
    role_name: str
    level: InterviewLevel
    total: int = Field(ge=3, le=4)
    questions: list[GeneratedQuestionItem] = Field(min_length=3, max_length=4)
    metadata: ServiceMetadata
    created_at: datetime

    @model_validator(mode="after")
    def ordered_questions(self):
        if self.total != len(self.questions):
            raise ValueError("Question count does not match total")
        if [q.order_index for q in self.questions] != list(range(1, self.total + 1)):
            raise ValueError("Question order must be consecutive")
        return self

"""
models.py — Pydantic v2 request/response schemas.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# ── Requests ──────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    user_id: str = Field(..., example="student_001")


class SubmitAnswerRequest(BaseModel):
    user_id:       str = Field(..., example="student_001")
    question_id:   str = Field(..., example="507f1f77bcf86cd799439011")
    chosen_answer: str = Field(..., example="5")


# ── Responses ─────────────────────────────────────────────────

class SessionOut(BaseModel):
    user_id:            str
    current_ability:    float
    questions_done:     int
    total_correct:      int
    is_complete:        bool
    is_new:             bool


class QuestionOut(BaseModel):
    question_id:    str
    text:           str
    choices:        list[str]
    topic:          str
    tags:           list[str]
    difficulty:     float
    round_number:   int
    current_theta:  float


class AnswerResult(BaseModel):
    is_correct:       bool
    correct_answer:   str
    explanation:      str
    old_theta:        float
    new_theta:        float
    direction:        str        # "harder" | "easier" | "same"
    questions_done:   int
    is_complete:      bool


class StudyPlanOut(BaseModel):
    summary:     str
    steps:       list[str]
    weak_topics: list[str]
    final_theta: float
    score:       str


class StatusOut(BaseModel):
    user_id:          str
    current_ability:  float
    ability_history:  list[dict]
    questions_done:   int
    total_correct:    int
    topic_stats:      dict
    is_complete:      bool

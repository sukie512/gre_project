"""
main.py — FastAPI backend for the GRE Adaptive Diagnostic Engine.

API Endpoints:
  GET  /health                    — Atlas ping + question count
  POST /session/start             — Create or resume a user session
  GET  /session/{user_id}         — Current session status
  GET  /next-question/{user_id}   — Next adaptive question
  POST /submit-answer             — Submit an answer, get feedback + new theta
  POST /study-plan/{user_id}      — Generate AI study plan (Phase 3)
  DELETE /session/{user_id}       — Reset session

Run:
    uvicorn backend.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bson import ObjectId
import os

from backend.database import questions_col, sessions_col, ping
from backend.models import (
    StartSessionRequest, SubmitAnswerRequest,
    SessionOut, QuestionOut, AnswerResult, StudyPlanOut, StatusOut,
)
from backend.adaptive import (
    get_or_create_session, next_question, record_answer,
    theta_direction, MAX_QUESTIONS,
)
from backend.llm import generate_study_plan

app = FastAPI(
    title="GRE Adaptive Diagnostic Engine",
    description="1D Adaptive Testing · IRT 2PL · AI Study Plans",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend/index.html at root
_frontend = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/static", StaticFiles(directory=_frontend), name="static")


# ── Health ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    db_ok = ping()
    q_count = questions_col.count_documents({}) if db_ok else 0
    return {
        "api":       "ok",
        "database":  "ok" if db_ok else "unreachable",
        "questions": q_count,
    }


# ── Session ────────────────────────────────────────────────────

@app.post("/session/start", response_model=SessionOut)
def start_session(body: StartSessionRequest):
    session, is_new = get_or_create_session(body.user_id)
    return SessionOut(
        user_id          = session["userId"],
        current_ability  = session["currentAbility"],
        questions_done   = session["totalQuestionsSeen"],
        total_correct    = session["totalCorrect"],
        is_complete      = session["isComplete"],
        is_new           = is_new,
    )


@app.get("/session/{user_id}", response_model=StatusOut)
def session_status(user_id: str):
    session = sessions_col.find_one({"userId": user_id})
    if not session:
        raise HTTPException(404, f"No session found for '{user_id}'")
    return StatusOut(
        user_id         = session["userId"],
        current_ability = session["currentAbility"],
        ability_history = session.get("abilityHistory", []),
        questions_done  = session["totalQuestionsSeen"],
        total_correct   = session["totalCorrect"],
        topic_stats     = session.get("topicStats", {}),
        is_complete     = session["isComplete"],
    )


@app.delete("/session/{user_id}")
def reset_session(user_id: str):
    sessions_col.delete_one({"userId": user_id})
    return {"message": f"Session for '{user_id}' reset."}


# ── Questions ──────────────────────────────────────────────────

@app.get("/next-question/{user_id}", response_model=QuestionOut)
def get_next_question(user_id: str):
    session = sessions_col.find_one({"userId": user_id})
    if not session:
        raise HTTPException(404, f"No session found for '{user_id}'. Call POST /session/start first.")
    if session["isComplete"]:
        raise HTTPException(400, "Session is complete. Call POST /study-plan/{user_id} for your plan.")

    seen   = session.get("seenIds", [])
    theta  = session["currentAbility"]
    q      = next_question(theta, seen)

    if not q:
        raise HTTPException(404, "No unseen questions available.")

    return QuestionOut(
        question_id   = str(q["_id"]),
        text          = q["text"],
        choices       = q["choices"],
        topic         = q.get("topic", ""),
        tags          = q.get("tags", []),
        difficulty    = q["difficulty"],
        round_number  = session["totalQuestionsSeen"] + 1,
        current_theta = round(theta, 4),
    )


# ── Submit Answer ──────────────────────────────────────────────

@app.post("/submit-answer", response_model=AnswerResult)
def submit_answer(body: SubmitAnswerRequest):
    session = sessions_col.find_one({"userId": body.user_id})
    if not session:
        raise HTTPException(404, f"No session for '{body.user_id}'")
    if session["isComplete"]:
        raise HTTPException(400, "Session already complete.")

    try:
        qid = ObjectId(body.question_id)
    except Exception:
        raise HTTPException(400, "Invalid question_id format.")

    question = questions_col.find_one({"_id": qid})
    if not question:
        raise HTTPException(404, "Question not found.")

    old_theta  = session["currentAbility"]
    session    = record_answer(session, question, body.chosen_answer)
    new_theta  = session["currentAbility"]

    return AnswerResult(
        is_correct     = body.chosen_answer.strip() == question["correct_answer"].strip(),
        correct_answer = question["correct_answer"],
        explanation    = question.get("explanation", ""),
        old_theta      = round(old_theta, 4),
        new_theta      = round(new_theta, 4),
        direction      = theta_direction(old_theta, new_theta),
        questions_done = session["totalQuestionsSeen"],
        is_complete    = session["isComplete"],
    )


# ── AI Study Plan (Phase 3) ────────────────────────────────────

@app.post("/study-plan/{user_id}", response_model=StudyPlanOut)
def study_plan(user_id: str):
    session = sessions_col.find_one({"userId": user_id})
    if not session:
        raise HTTPException(404, f"No session for '{user_id}'")
    if not session["isComplete"] and session["totalQuestionsSeen"] < 3:
        raise HTTPException(400, "Complete at least 3 questions before generating a study plan.")

    try:
        plan = generate_study_plan(session)
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

    total   = session["totalQuestionsSeen"]
    correct = session["totalCorrect"]
    return StudyPlanOut(
        summary     = plan.get("summary", ""),
        steps       = plan.get("steps", [])[:3],
        weak_topics = plan.get("weak_topics", []),
        final_theta = round(session["currentAbility"], 4),
        score       = f"{correct}/{total}",
    )


# ── Frontend fallback ──────────────────────────────────────────

@app.get("/")
def serve_frontend():
    idx = os.path.join(_frontend, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"message": "GRE Adaptive Engine API — visit /docs for Swagger UI"}

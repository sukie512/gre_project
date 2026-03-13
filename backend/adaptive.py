"""
adaptive.py — Phase 2: 1D Adaptive Logic using IRT 2-Parameter Logistic Model.

IRT 2PL Formula:
    P(correct | theta, a, b) = 1 / (1 + exp(-a * (theta - b)))

    theta : student ability  [0.05 – 0.95]
    a     : discrimination   (how well the item separates ability levels)
    b     : difficulty       [0.1  – 1.0]

Ability Update: Newton-Raphson Maximum Likelihood Estimation over the full
response history:
    theta_new = theta - lr * (dLogL/dTheta) / (d²LogL/dTheta²)
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from bson import ObjectId

from backend.database import questions_col, sessions_col

MAX_QUESTIONS  = 10
BASELINE_THETA = 0.5


# ── IRT 2PL Math ───────────────────────────────────────────────

def irt_p(theta: float, b: float, a: float = 1.0) -> float:
    """Probability of a correct response under the 2PL model."""
    return 1.0 / (1.0 + math.exp(-a * (theta - b)))


def newton_raphson_mle(
    theta: float,
    history: list[dict],
    lr: float = 0.3,
    max_iter: int = 10,
) -> float:
    """
    Update ability estimate via Newton-Raphson MLE over full response history.
    history items: { b: float, a: float, correct: bool }
    Returns new theta clamped to [0.05, 0.95].
    """
    for _ in range(max_iter):
        d1 = 0.0   # first derivative of log-likelihood
        d2 = 0.0   # second derivative (negative Fisher information)
        for r in history:
            p   = irt_p(theta, r["b"], r["a"])
            u   = 1.0 if r["correct"] else 0.0
            d1 += r["a"] * (u - p)
            d2 -= r["a"] ** 2 * p * (1.0 - p)
        if d2 == 0.0:
            break
        theta -= lr * (d1 / d2)

    return max(0.05, min(0.95, theta))


# ── Question Selection ─────────────────────────────────────────

def next_question(theta: float, seen_ids: list[ObjectId]) -> dict | None:
    """
    Select the unseen question with difficulty closest to current theta.
    This maximises Fisher information (most informative item selection).
    """
    pipeline = [
        {"$match": {"_id": {"$nin": seen_ids}}},
        {"$addFields": {"gap": {"$abs": {"$subtract": ["$difficulty", theta]}}}},
        {"$sort": {"gap": 1}},
        {"$limit": 1},
    ]
    result = list(questions_col.aggregate(pipeline))
    return result[0] if result else None


# ── Session Management ─────────────────────────────────────────

def get_or_create_session(user_id: str) -> tuple[dict, bool]:
    """
    Load existing session or create a new one at theta=0.5.
    Returns (session_doc, is_new).
    """
    existing = sessions_col.find_one({"userId": user_id})
    if existing:
        return existing, False

    now = datetime.now(timezone.utc)
    doc = {
        "userId":             user_id,
        "currentAbility":     BASELINE_THETA,
        "abilityHistory":     [{"step": 0, "ability": BASELINE_THETA, "timestamp": now}],
        "irtHistory":         [],
        "questionHistory":    [],
        "seenIds":            [],
        "totalQuestionsSeen": 0,
        "totalCorrect":       0,
        "topicStats":         {},
        "isComplete":         False,
        "createdAt":          now,
        "updatedAt":          now,
    }
    sessions_col.insert_one(doc)
    return sessions_col.find_one({"userId": user_id}), True


def record_answer(session: dict, question: dict, chosen: str) -> dict:
    """
    Score the answer, run Newton-Raphson MLE, persist full history to MongoDB.
    Returns the refreshed session document.
    """
    now        = datetime.now(timezone.utc)
    is_correct = chosen.strip() == question["correct_answer"].strip()
    old_theta  = session["currentAbility"]

    # Append new IRT entry
    irt_entry = {
        "b":       question["difficulty"],
        "a":       question.get("discrimination", 1.0),
        "correct": is_correct,
    }
    updated_irt = list(session.get("irtHistory", [])) + [irt_entry]

    # Recalculate ability over full history
    new_theta = newton_raphson_mle(old_theta, updated_irt)

    # Update topic stats
    topic     = question.get("topic", "General")
    ts        = dict(session.get("topicStats", {}).get(topic, {"seen": 0, "correct": 0}))
    ts["seen"]    += 1
    ts["correct"] += 1 if is_correct else 0

    new_done    = session["totalQuestionsSeen"] + 1
    is_complete = new_done >= MAX_QUESTIONS

    history_entry = {
        "questionId":     question["_id"],
        "topic":          topic,
        "tags":           question.get("tags", []),
        "difficulty":     question["difficulty"],
        "chosenAnswer":   chosen,
        "correctAnswer":  question["correct_answer"],
        "isCorrect":      is_correct,
        "abilityBefore":  round(old_theta, 4),
        "abilityAfter":   round(new_theta, 4),
        "answeredAt":     now,
    }

    sessions_col.update_one(
        {"userId": session["userId"]},
        {
            "$set": {
                "currentAbility":            new_theta,
                "isComplete":                is_complete,
                "updatedAt":                 now,
                f"topicStats.{topic}":       ts,
            },
            "$push": {
                "irtHistory":      irt_entry,
                "questionHistory": history_entry,
                "abilityHistory":  {
                    "step":      new_done,
                    "ability":   round(new_theta, 4),
                    "correct":   is_correct,
                    "timestamp": now,
                },
                "seenIds": question["_id"],
            },
            "$inc": {
                "totalQuestionsSeen": 1,
                "totalCorrect":       1 if is_correct else 0,
            },
        },
    )

    return sessions_col.find_one({"userId": session["userId"]})


def theta_direction(old: float, new: float) -> str:
    """Return human-readable direction of ability change."""
    if new > old + 0.005:
        return "harder"
    if new < old - 0.005:
        return "easier"
    return "same"

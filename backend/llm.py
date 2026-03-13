"""
llm.py — Phase 3: AI Insights via Anthropic Claude.

Sends completed session performance data to Claude and gets back
a structured 3-step personalised study plan.
"""
from __future__ import annotations
import os, json
import anthropic
from dotenv import load_dotenv

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def generate_study_plan(session: dict) -> dict:
    """
    Build a rich performance prompt → call Claude → parse JSON.
    Returns: { summary: str, steps: [str,str,str], weak_topics: [str] }
    """
    total   = session["totalQuestionsSeen"]
    correct = session["totalCorrect"]
    theta   = session["currentAbility"]
    pct     = round(correct / total * 100) if total else 0

    topic_lines, weak_topics = [], []
    for topic, stat in session.get("topicStats", {}).items():
        tp = round(stat["correct"] / stat["seen"] * 100) if stat["seen"] else 0
        topic_lines.append(f"  - {topic}: {stat['correct']}/{stat['seen']} correct ({tp}%)")
        if stat["seen"] > 0 and stat["correct"] / stat["seen"] < 0.6:
            weak_topics.append(topic)

    theta_prog = " → ".join(
        str(round(h["ability"], 3))
        for h in session.get("abilityHistory", [])
    )

    prompt = f"""You are an expert GRE tutor reviewing a student's adaptive diagnostic.

STUDENT PERFORMANCE DATA:
- Student ID      : {session["userId"]}
- Final ability θ : {theta:.3f}  (scale 0.0–1.0, baseline = 0.5)
- Score           : {correct}/{total} ({pct}%)
- θ progression   : {theta_prog}
- Topic results   :
{chr(10).join(topic_lines) if topic_lines else "  No topic data"}
- Topics needing work (<60%): {", ".join(weak_topics) if weak_topics else "None — great overall performance!"}

Generate a concise, specific, actionable 3-step personalised study plan.

Guidelines:
- If θ > 0.70: focus on advanced GRE strategy (timing, hard question types), not basics.
- If θ < 0.40: start with foundational resources and concept review.
- Reference the student's actual weak topics in each step.
- Be specific — mention real GRE resources, practice strategies, question types.

Respond ONLY with valid JSON (no markdown, no text before/after the object):
{{"summary":"one-sentence performance overview","steps":["Step 1: ...","Step 2: ...","Step 3: ..."],"weak_topics":["topic1","topic2"]}}"""

    msg = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)

    steps = data.get("steps", [])
    while len(steps) < 3:
        steps.append("Review all missed questions and re-attempt similar problems.")
    data["steps"] = steps[:3]
    return data

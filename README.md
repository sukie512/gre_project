# GRE Adaptive Diagnostic Engine

> Intern Assignment — AI-Driven Adaptive Testing Prototype  
> Stack: Python · FastAPI · MongoDB Atlas · Anthropic Claude · Vanilla JS

---

## Project Structure

```
gre_project/
├── backend/
│   ├── main.py        # FastAPI app — all 7 API endpoints
│   ├── database.py    # MongoDB Atlas singleton (questions + userSessions)
│   ├── models.py      # Pydantic v2 request/response schemas
│   ├── adaptive.py    # IRT 2PL engine + Newton-Raphson MLE + session logic
│   ├── llm.py         # Anthropic Claude integration (Phase 3 study plan)
│   └── seed.py        # Seeds 20 GRE questions + creates indexes
├── frontend/
│   └── index.html     # Single-page UI (served by FastAPI at GET /)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## How to Run

### 1. Clone & install

```bash
git clone <your-repo-url>
cd gre_project
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/...
#   ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Seed the database (run once)

```bash
python backend/seed.py
```

This drops + recreates the `questions` and `userSessions` collections,
inserts 20 GRE questions, and creates indexes.

### 4. Start the server

```bash
uvicorn backend.main:app --reload
```

### 5. Open the app

- **Frontend UI** → http://localhost:8000  
- **Swagger API docs** → http://localhost:8000/docs  

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Atlas ping + question count |
| POST | `/session/start` | Create or resume a user session |
| GET | `/session/{user_id}` | Session status, topic stats, ability history |
| DELETE | `/session/{user_id}` | Reset / delete session |
| GET | `/next-question/{user_id}` | Next adaptive question (IRT selection) |
| POST | `/submit-answer` | Submit answer → score + update θ |
| POST | `/study-plan/{user_id}` | Generate AI study plan via Claude |

---

## Adaptive Algorithm (Phase 2)

### IRT 2-Parameter Logistic Model

```
P(correct | θ, a, b) = 1 / (1 + exp(−a × (θ − b)))
```

| Symbol | Meaning | Range |
|--------|---------|-------|
| θ (theta) | Student ability estimate | 0.05 – 0.95 |
| a | Discrimination (question sensitivity) | 1.0 – 1.2 |
| b | Difficulty | 0.20 – 0.65 |

### Ability Update — Newton-Raphson MLE

After each answer, θ is updated by maximising the log-likelihood over the
**full response history**:

```
θ_new = θ − lr × (dLogL/dθ) / (d²LogL/dθ²)
```

- `lr = 0.3`, `max_iter = 10`
- θ is clamped to `[0.05, 0.95]`
- **Correct answer** → next question will be harder (higher b)
- **Incorrect answer** → next question will be easier (lower b)

### Question Selection

The unseen question with `|difficulty − θ|` minimised is selected next.
This is equivalent to the maximum Fisher-information criterion — the most
informative question given the current ability estimate.

---

## AI Study Plan (Phase 3)

After 10 questions, the student's full performance data (topics missed,
accuracy per topic, θ progression, score) is sent to **Claude claude-opus-4-6**.

The prompt asks Claude to return structured JSON:

```json
{
  "summary": "one-sentence overview",
  "steps":   ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "weak_topics": ["Vocabulary", "Algebra"]
}
```

The plan adapts to ability level:
- θ > 0.70 → advanced GRE strategy (timing, hard question types)
- θ < 0.40 → foundational resources and concept review

---

## AI Log

**Tools used:** Claude (Anthropic) via claude.ai

**What AI accelerated:**
- Initial project scaffolding and file structure
- IRT 2PL formula implementation and Newton-Raphson derivation check
- MongoDB aggregation pipeline for question selection
- Pydantic schema design
- Frontend JS state management

**Challenges AI couldn't solve:**
- PDF text extraction (custom glyph encoding required manual CMap decoding)
- MongoDB Atlas connection string debugging (environment-specific)
- CORS configuration for `file://` vs `http://` origins
- Exact Pydantic v2 vs v1 API differences required manual testing

---

## Evaluation Criteria Coverage

| Criteria | Implementation |
|----------|---------------|
| System Design | Clean collection schema with indexes; UserSession tracks full history |
| Algorithmic Logic | Mathematically sound IRT 2PL + Newton-Raphson MLE (not random jumps) |
| AI Proficiency | Structured JSON prompt with performance context; handles θ-adaptive plan |
| Code Hygiene | `.env` for secrets; Pydantic typing; modular separation; error handling |

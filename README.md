# GRE Adaptive Diagnostic Engine

Built this as part of the intern assignment. The idea is a 10-question GRE quiz that gets harder or easier based on how you're doing — not randomly, but using actual Item Response Theory math. After you finish, Claude generates a personalised study plan based on your weak spots.

Stack: Python, FastAPI, MongoDB Atlas, Anthropic Claude API, plain HTML/JS frontend.

---

## What it does

You enter a student ID, answer 10 GRE questions, and the system tracks your ability score (θ) after every answer. Get one right and the next question is harder. Get one wrong and it pulls back to something easier. At the end you see your score breakdown by topic and can generate an AI study plan.

The three phases from the assignment:
- **Phase 1** — MongoDB data model with 20 GRE questions (Algebra, Vocabulary, Geometry, Reading Comprehension etc.), each with difficulty and discrimination parameters
- **Phase 2** — Adaptive question selection using IRT 2PL + Newton-Raphson MLE to estimate ability
- **Phase 3** — Claude generates a 3-step study plan based on your actual performance data

---

## Project structure

```
gre_project/
├── backend/
│   ├── main.py        # FastAPI — 7 API endpoints
│   ├── database.py    # MongoDB Atlas connection
│   ├── models.py      # Pydantic schemas
│   ├── adaptive.py    # IRT 2PL algorithm + ability estimation
│   ├── llm.py         # Claude API integration
│   └── seed.py        # Seeds 20 questions into MongoDB
├── frontend/
│   └── index.html     # Single page UI served by FastAPI
├── requirements.txt
├── .env.example
└── README.md
```

---

## How to run it

You need Python 3.10+, a MongoDB Atlas account (free tier works), and an Anthropic API key.

**1. Clone and install dependencies**
```bash
git clone https://github.com/sukie512/gre_project
cd gre_project
pip install -r requirements.txt
```

**2. Set up your .env file**

Copy `.env.example` to `.env` and fill in your credentials:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
ANTHROPIC_API_KEY=sk-ant-api03-...
```

To get your MongoDB URI: go to cloud.mongodb.com → your cluster → Connect → Drivers → copy the string and replace `<password>` with your actual password.

To get your Anthropic key: go to console.anthropic.com → API Keys → Create Key.

**3. Seed the database (only needed once)**
```bash
py -m backend.seed
```

This creates the `questions` and `userSessions` collections and loads 20 GRE questions with proper indexes.

**4. Start the server**
```bash
uvicorn backend.main:app --reload
```

**5. Open in browser**
- UI → http://localhost:8000
- API docs → http://localhost:8000/docs

---

## API endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/health` | Check if server + DB are connected |
| POST | `/session/start` | Start or resume a session for a student |
| GET | `/session/{user_id}` | Get full session data, scores, topic breakdown |
| DELETE | `/session/{user_id}` | Reset a session |
| GET | `/next-question/{user_id}` | Get next question based on current ability |
| POST | `/submit-answer` | Submit answer, get feedback + updated θ |
| POST | `/study-plan/{user_id}` | Generate Claude study plan |

---

## How the adaptive algorithm works (Phase 2)

The core formula is the IRT 2-Parameter Logistic model:

```
P(correct | θ, a, b) = 1 / (1 + exp(−a × (θ − b)))
```

Where θ is the student's estimated ability (starts at 0.5), b is question difficulty (0.20–0.65), and a is discrimination (how sensitive the question is to ability differences).

After each answer, θ gets updated using Newton-Raphson MLE — basically it looks at your full answer history and finds the ability value that best explains everything you've answered so far:

```
θ_new = θ − lr × (first derivative of log-likelihood) / (second derivative)
```

Learning rate is 0.3, clamped to [0.05, 0.95] so it never goes to extremes.

For question selection, the system picks the unseen question where `|difficulty − θ|` is smallest — meaning it always gives you the most informative question for your current level.

---

## How the AI study plan works (Phase 3)

After 10 questions, your full performance data gets sent to Claude — your θ progression, score per topic, which topics you struggled with, how your ability changed over time. Claude returns a structured JSON response with a summary, 3 specific study steps, and a list of weak topics to focus on.

The prompt changes based on your ability level:
- If θ > 0.70, the plan focuses on advanced strategy and hard question types
- If θ < 0.40, it focuses on foundational concepts and basic review

---

## AI log

I used Claude (claude.ai) throughout this project. Here's an honest breakdown of where it helped and where it didn't:

**Where AI actually saved time:**
- Writing the IRT 2PL formula and Newton-Raphson implementation — I understood the math conceptually but implementing it cleanly in Python would have taken much longer
- Setting up the FastAPI boilerplate and Pydantic schemas
- Writing the 20 GRE questions with realistic difficulty values and explanations
- Frontend JavaScript state management — the session flow logic
- Structuring the Claude prompt to return consistent JSON

**Where I had to figure things out myself:**
- MongoDB Atlas connection kept failing because of IP whitelist settings — AI kept giving generic advice, had to find the Network Access setting myself
- Python 3.14 compatibility broke pydantic-core during install — had to manually figure out to install without pinned versions
- Import paths kept breaking when running uvicorn from different directories — took a while to figure out the `backend.module` vs `module` issue
- The frontend submit button wasn't working because choices with apostrophes were breaking the `onclick` attribute string — had to debug that in browser console

Overall the project took longer than expected mostly because of environment setup issues, not the actual coding. The algorithm and API parts came together pretty cleanly once everything was running.

---

## Evaluation criteria

| What was asked | What I built |
|----------------|--------------|
| MongoDB data model | Two collections — `questions` (20 GRE questions with IRT params) and `userSessions` (full history per student). Indexes on topic+difficulty and userId. |
| Adaptive algorithm | Proper IRT 2PL with Newton-Raphson MLE. Not just "go harder if correct" — it estimates actual ability from the full response history. |
| AI integration | Claude gets your real performance data and returns a structured, personalised plan. Prompt adapts based on θ level. |
| Code quality | Secrets in .env, Pydantic typing throughout, modular backend (database/models/adaptive/llm all separate), error handling on every endpoint. |

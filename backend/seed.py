"""
seed.py — Phase 1: Seeds 20 GRE-style questions into MongoDB.

Run ONCE before starting the server:
    python backend/seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from backend.database import questions_col, sessions_col, ping

QUESTIONS = [
    # ── Easy (difficulty 0.2–0.35) ──────────────────────────────
    {
        "text":           "If 2x + 3 = 13, what is the value of x?",
        "choices":        ["3", "4", "5", "6"],
        "correct_answer": "5",
        "difficulty":     0.30,
        "discrimination": 1.0,
        "topic":          "Algebra",
        "tags":           ["linear-equations", "quant"],
        "explanation":    "2x + 3 = 13 → 2x = 10 → x = 5.",
    },
    {
        "text":           "What is 15% of 80?",
        "choices":        ["10", "12", "15", "18"],
        "correct_answer": "12",
        "difficulty":     0.25,
        "discrimination": 1.0,
        "topic":          "Arithmetic",
        "tags":           ["percentages", "quant"],
        "explanation":    "0.15 × 80 = 12.",
    },
    {
        "text":           "A car travels 120 miles in 3 hours. What is its average speed in mph?",
        "choices":        ["30", "35", "40", "45"],
        "correct_answer": "40",
        "difficulty":     0.20,
        "discrimination": 1.0,
        "topic":          "Word Problems",
        "tags":           ["rate", "distance", "quant"],
        "explanation":    "Speed = distance / time = 120 / 3 = 40 mph.",
    },
    {
        "text":           "A rectangle has a length of 8 and a width of 5. What is its area?",
        "choices":        ["13", "20", "30", "40"],
        "correct_answer": "40",
        "difficulty":     0.20,
        "discrimination": 1.0,
        "topic":          "Geometry",
        "tags":           ["area", "quant"],
        "explanation":    "Area = length × width = 8 × 5 = 40.",
    },
    {
        "text":           "What is the value of 2^3 × 2^2?",
        "choices":        ["2^5", "2^6", "2^7", "2^8"],
        "correct_answer": "2^5",
        "difficulty":     0.30,
        "discrimination": 1.0,
        "topic":          "Algebra",
        "tags":           ["exponents", "quant"],
        "explanation":    "Add exponents when multiplying same base: 2^(3+2) = 2^5.",
    },
    {
        "text":           "A class has 12 boys and 18 girls. What percentage of the class are girls?",
        "choices":        ["40%", "50%", "60%", "70%"],
        "correct_answer": "60%",
        "difficulty":     0.30,
        "discrimination": 1.0,
        "topic":          "Data Analysis",
        "tags":           ["percentages", "quant"],
        "explanation":    "Total = 30. Girls: 18/30 = 60%.",
    },
    {
        "text":           "A fair die is rolled once. What is the probability of rolling an even number?",
        "choices":        ["1/6", "1/3", "1/2", "2/3"],
        "correct_answer": "1/2",
        "difficulty":     0.30,
        "discrimination": 1.0,
        "topic":          "Probability",
        "tags":           ["basic-probability", "quant"],
        "explanation":    "Even outcomes: {2,4,6} = 3 out of 6 = 1/2.",
    },
    # ── Medium (difficulty 0.35–0.55) ───────────────────────────
    {
        "text":           "If x + y = 10 and x − y = 4, what is the value of x?",
        "choices":        ["3", "5", "7", "9"],
        "correct_answer": "7",
        "difficulty":     0.35,
        "discrimination": 1.0,
        "topic":          "Algebra",
        "tags":           ["systems-of-equations", "quant"],
        "explanation":    "Add equations: 2x = 14 → x = 7.",
    },
    {
        "text":           "The ratio of cats to dogs at a shelter is 3:5. If there are 24 cats, how many dogs are there?",
        "choices":        ["30", "32", "36", "40"],
        "correct_answer": "40",
        "difficulty":     0.35,
        "discrimination": 1.0,
        "topic":          "Ratios & Proportions",
        "tags":           ["ratios", "quant"],
        "explanation":    "3:5 = 24:x → x = 40.",
    },
    {
        "text":           "A circle has a radius of 7. What is its circumference? (Use π ≈ 3.14)",
        "choices":        ["21.98", "38.48", "43.96", "49.34"],
        "correct_answer": "43.96",
        "difficulty":     0.40,
        "discrimination": 1.0,
        "topic":          "Geometry",
        "tags":           ["circles", "quant"],
        "explanation":    "C = 2πr = 2 × 3.14 × 7 = 43.96.",
    },
    {
        "text":           "If 3x − 5 > 7, which must be true?",
        "choices":        ["x > 4", "x > 2", "x < 4", "x < 2"],
        "correct_answer": "x > 4",
        "difficulty":     0.40,
        "discrimination": 1.0,
        "topic":          "Algebra",
        "tags":           ["inequalities", "quant"],
        "explanation":    "3x − 5 > 7 → 3x > 12 → x > 4.",
    },
    {
        "text":           "A study found that people who read regularly tend to have larger vocabularies. This most strongly supports which statement?",
        "choices":        [
            "Reading causes people to become more intelligent.",
            "People with larger vocabularies always read regularly.",
            "Regular reading is associated with larger vocabularies.",
            "Reading is the only way to increase vocabulary.",
        ],
        "correct_answer": "Regular reading is associated with larger vocabularies.",
        "difficulty":     0.45,
        "discrimination": 1.1,
        "topic":          "Reading Comprehension",
        "tags":           ["inference", "verbal"],
        "explanation":    "The study shows correlation, not causation.",
    },
    {
        "text":           "If f(x) = x² − 4x + 3, what is f(5)?",
        "choices":        ["4", "5", "8", "10"],
        "correct_answer": "8",
        "difficulty":     0.45,
        "discrimination": 1.0,
        "topic":          "Algebra",
        "tags":           ["functions", "quant"],
        "explanation":    "f(5) = 25 − 20 + 3 = 8.",
    },
    {
        "text":           "The committee found her report to be so ___ that they requested a shorter summary.",
        "choices":        ["succinct", "laconic", "prolix", "pithy"],
        "correct_answer": "prolix",
        "difficulty":     0.50,
        "discrimination": 1.1,
        "topic":          "Vocabulary",
        "tags":           ["text-completion", "verbal"],
        "explanation":    "Prolix = excessively wordy.",
    },
    {
        "text":           "An article argues that technology can facilitate communication but may lead to more superficial interactions. What is the author's primary concern?",
        "choices":        [
            "Technology should be banned in social settings.",
            "Technology makes all communication more efficient.",
            "Technology can undermine the depth of human interaction.",
            "Technology has no effect on how people communicate.",
        ],
        "correct_answer": "Technology can undermine the depth of human interaction.",
        "difficulty":     0.50,
        "discrimination": 1.1,
        "topic":          "Reading Comprehension",
        "tags":           ["main-idea", "verbal"],
        "explanation":    "The concern is loss of depth, not a ban on technology.",
    },
    # ── Hard (difficulty 0.55–0.80) ─────────────────────────────
    {
        "text":           "The CEO's remarks were so ___ that even her supporters found it difficult to discern her actual position.",
        "choices":        ["incisive", "opaque", "lucid", "straightforward", "pellucid"],
        "correct_answer": "opaque",
        "difficulty":     0.55,
        "discrimination": 1.1,
        "topic":          "Vocabulary",
        "tags":           ["text-completion", "verbal"],
        "explanation":    "Opaque = unclear / impossible to interpret.",
    },
    {
        "text":           "Unlike her more ___ colleagues who openly challenged the proposal, Maria remained silent.",
        "choices":        ["vociferous", "retiring", "timid", "diffident"],
        "correct_answer": "vociferous",
        "difficulty":     0.55,
        "discrimination": 1.1,
        "topic":          "Vocabulary",
        "tags":           ["text-completion", "verbal"],
        "explanation":    "Vociferous = loudly outspoken. Contrasts with Maria's silence.",
    },
    {
        "text":           "Although the professor was known for his ___, his lectures were surprisingly engaging.",
        "choices":        ["eloquence", "verbosity", "pedantry", "aplomb", "reticence"],
        "correct_answer": "pedantry",
        "difficulty":     0.60,
        "discrimination": 1.2,
        "topic":          "Vocabulary",
        "tags":           ["sentence-completion", "verbal"],
        "explanation":    "Pedantry (overemphasis on minor details) contrasts with 'surprisingly engaging'.",
    },
    {
        "text":           "The reviewer's praise for the novel was so ___ that readers were surprised when she admitted finding the plot predictable.",
        "choices":        ["effusive", "grudging", "tepid", "equivocal"],
        "correct_answer": "effusive",
        "difficulty":     0.65,
        "discrimination": 1.2,
        "topic":          "Vocabulary",
        "tags":           ["tone", "verbal"],
        "explanation":    "Effusive = enthusiastically gushing, contrasting with finding the plot predictable.",
    },
    {
        "text":           "Her explanation was so ___ that listeners were left more confused than enlightened.",
        "choices":        ["convoluted", "limpid", "transparent", "coherent"],
        "correct_answer": "convoluted",
        "difficulty":     0.50,
        "discrimination": 1.1,
        "topic":          "Vocabulary",
        "tags":           ["vocabulary", "verbal"],
        "explanation":    "Convoluted = unnecessarily complex and hard to follow.",
    },
]


def seed():
    if not ping():
        print("ERROR: Cannot reach MongoDB. Check your MONGO_URI in .env")
        sys.exit(1)

    questions_col.drop()
    sessions_col.drop()
    print("Dropped existing collections.")

    now  = datetime.now(timezone.utc)
    docs = [{**q, "createdAt": now, "updatedAt": now} for q in QUESTIONS]
    res  = questions_col.insert_many(docs)
    print(f"Inserted {len(res.inserted_ids)} questions.")

    # Indexes
    questions_col.create_index([("topic", 1), ("difficulty", 1)])
    sessions_col.create_index([("userId", 1)], unique=True)
    print("Indexes created.")
    print("\nDone. Now run:  uvicorn backend.main:app --reload")


if __name__ == "__main__":
    seed()

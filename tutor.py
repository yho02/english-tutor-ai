import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REVIEW_EVERY = 6

# ─── Default State ────────────────────────────────────────────────────────────

def default_profile() -> dict:
    return {
        "level": "unknown",
        "grammar_score": 0.5,
        "vocabulary_score": 0.5,
        "exchange_count": 0,
        "learned_topics": [],
        "last_review_at": 0,
    }

def default_state() -> dict:
    return {
        "conversation_history": [],
        "student_profile": default_profile(),
    }

# ─── System Prompt ────────────────────────────────────────────────────────────

def get_system_prompt(profile: dict, lesson: dict = None) -> str:
    level_guidance = {
        "unknown":      "You don't know the student's level yet. Start simple, observe, and infer.",
        "beginner":     "Use very simple words and short sentences. Avoid jargon. Be very encouraging.",
        "intermediate": "Use moderate vocabulary. Explain grammar terms briefly. Balance challenge with support.",
        "advanced":     "Use precise linguistic terminology. Offer nuanced, detailed explanations. Challenge them.",
    }

    learned  = ", ".join([t["topic"] for t in profile["learned_topics"]]) or "none yet"
    mastered = ", ".join([t["topic"] for t in profile["learned_topics"] if t["mastered"]]) or "none yet"

    lesson_guidance = ""
    if lesson:
        example = lesson.get("example_sentence") or "N/A"
        lesson_guidance = f"""
CURRENT CURRICULUM GOAL (hidden from student):
- CEFR Level: {lesson.get('cefr_level', 'N/A')}
- Grammar focus: {lesson.get('guideword', 'N/A')}
- Objective: {lesson.get('learning_objective', 'N/A')}
- Example sentence to model naturally: "{example}"

Steer the conversation naturally toward this grammar point.
Never announce it. Let the student discover it through practice.
"""

    return f"""You are an adaptive English grammar tutor. Your job is to teach English in a personalised, encouraging way.

STUDENT PROFILE (update your behaviour based on this):
- Detected level: {profile['level']}
- Grammar strength: {profile['grammar_score']:.0%} ({'strong' if profile['grammar_score'] > 0.65 else 'needs work'})
- Vocabulary strength: {profile['vocabulary_score']:.0%} ({'strong' if profile['vocabulary_score'] > 0.65 else 'needs work'})
- Topics introduced: {learned}
- Topics mastered: {mastered}

LEVEL GUIDANCE:
{level_guidance.get(profile['level'], level_guidance['unknown'])}

YOUR TASKS (pick the most relevant one per turn):
1. CORRECTION — If the student's sentence has errors, identify each error, explain it simply, and show the corrected version.
2. PRAISE — If the sentence is correct, confirm it warmly and briefly explain WHY it is correct.
3. CHALLENGE — When the student does well, introduce a slightly harder concept or vocabulary word related to their topic.
4. REVIEW — Every 6 exchanges (you will be explicitly asked for a review), summarise what the student has learned, what they're strong at, and give them a short exercise to test a weakness.

ADAPTATION RULES:
- If the student makes the SAME error twice, try a different explanation strategy.
- If grammar is strong but vocabulary is weak, introduce new words proactively.
- If vocabulary is strong but grammar is weak, focus corrections on grammar patterns.
- After a topic is introduced 3+ times correctly, consider it mastered.

ALWAYS end each response with a short, gentle invitation for the student to try another sentence.
{lesson_guidance}"""

# ─── Profile Updater ──────────────────────────────────────────────────────────

def update_profile(profile: dict, user_sentence: str, tutor_reply: str) -> dict:
    """
    Calls the LLM to extract assessment signals and mutates `profile` in place.
    Returns the updated profile (also mutated in place for convenience).
    """
    probe = f"""
You are an assessment engine. Given a student sentence and a tutor reply, return ONLY valid JSON (no markdown, no extra text) with these fields:

{{
  "level_signal": "beginner" | "intermediate" | "advanced" | "unknown",
  "grammar_ok": true | false,
  "vocabulary_ok": true | false,
  "topic_introduced": "<short topic name or null>",
  "topic_mastered": true | false
}}

Student sentence: {user_sentence}
Tutor reply: {tutor_reply}
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": probe}],
            max_tokens=200,
            temperature=0.1,
        )
        raw = res.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        signals = json.loads(raw)

        profile["exchange_count"] += 1

        level_map = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0, "unknown": None}
        lv = level_map.get(signals.get("level_signal", "unknown"))
        if lv is not None:
            alpha = 0.2 if profile["exchange_count"] > 5 else 0.4
            current_lv = level_map.get(profile["level"], 0.5) if profile["level"] != "unknown" else lv
            blended = (1 - alpha) * current_lv + alpha * lv
            if blended < 0.25:
                profile["level"] = "beginner"
            elif blended < 0.75:
                profile["level"] = "intermediate"
            else:
                profile["level"] = "advanced"

        smooth = 0.25
        if signals.get("grammar_ok") is True:
            profile["grammar_score"] = min(1.0, profile["grammar_score"] + smooth * (1 - profile["grammar_score"]))
        elif signals.get("grammar_ok") is False:
            profile["grammar_score"] = max(0.0, profile["grammar_score"] - smooth * profile["grammar_score"])

        if signals.get("vocabulary_ok") is True:
            profile["vocabulary_score"] = min(1.0, profile["vocabulary_score"] + smooth * (1 - profile["vocabulary_score"]))
        elif signals.get("vocabulary_ok") is False:
            profile["vocabulary_score"] = max(0.0, profile["vocabulary_score"] - smooth * profile["vocabulary_score"])

        topic = signals.get("topic_introduced")
        if topic and topic != "null":
            existing = next((t for t in profile["learned_topics"] if t["topic"] == topic), None)
            if existing:
                if signals.get("topic_mastered"):
                    existing["mastered"] = True
            else:
                profile["learned_topics"].append({"topic": topic, "mastered": bool(signals.get("topic_mastered"))})

    except Exception:
        profile["exchange_count"] += 1

    return profile

# ─── Core LLM Calls ───────────────────────────────────────────────────────────

def ask_tutor(sentence: str, history: list, profile: dict, lesson: dict = None) -> tuple[str, list]:
    """
    Sends the student sentence to the tutor LLM.
    Returns (reply_text, updated_history).
    """
    history = history + [{"role": "user", "content": sentence}]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt(profile, lesson)},
            *history,
        ],
    )
    reply = response.choices[0].message.content
    history = history + [{"role": "assistant", "content": reply}]
    return reply, history


def ask_for_review(history: list, profile: dict, lesson: dict = None) -> tuple[str, list, dict]:
    """
    Triggers a periodic progress review.
    Returns (review_text, updated_history, updated_profile).
    """
    learned  = ", ".join([t["topic"] for t in profile["learned_topics"]]) or "general English"
    weak_parts = []
    if profile["grammar_score"] < 0.5:
        weak_parts.append("grammar")
    if profile["vocabulary_score"] < 0.5:
        weak_parts.append("vocabulary")
    weak_str = " and ".join(weak_parts) if weak_parts else "no specific weakness detected"

    review_prompt = (
        f"Please give the student a friendly progress review. "
        f"Topics covered: {learned}. Areas needing more work: {weak_str}. "
        f"End with one short exercise sentence for the student to correct or complete."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt(profile, lesson)},
            *history,
            {"role": "user", "content": review_prompt},
        ],
    )
    reply = response.choices[0].message.content
    formatted = f"📊 **Progress Review**\n\n{reply}"

    history = history + [{"role": "assistant", "content": formatted}]
    profile["last_review_at"] = profile["exchange_count"]
    return formatted, history, profile


def is_review_due(profile: dict) -> bool:
    return (
        profile["exchange_count"] > 0
        and profile["exchange_count"] % REVIEW_EVERY == 0
        and profile["exchange_count"] != profile["last_review_at"]
    )


INITIAL_GREETING = (
    "Hello! I'm your English grammar tutor. 👋\n\n"
    "To get started, simply type any English sentence — it can be about any topic you'd like. "
    "I'll give you friendly feedback, correct any mistakes, and help you improve.\n\n"
    "Go ahead, try your first sentence!"
)
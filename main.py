import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(page_title="English Grammar Tutor", page_icon="📚", layout="centered")
st.title("📚 English Grammar Tutor")

# ─── Session State Init ──────────────────────────────────────────────────────
defaults = {
    "conversation_history": [],
    "student_profile": {
        "level": "unknown",           # beginner | intermediate | advanced
        "grammar_score": 0.5,         # 0.0 (weak) → 1.0 (strong)
        "vocabulary_score": 0.5,
        "exchange_count": 0,
        "learned_topics": [],         # list of {"topic": str, "mastered": bool}
        "last_review_at": 0,          # exchange_count when last review was given
    },
    "show_profile": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── System Prompt ────────────────────────────────────────────────────────────
def get_system_prompt():
    p = st.session_state.student_profile

    level_guidance = {
        "unknown":      "You don't know the student's level yet. Start simple, observe, and infer.",
        "beginner":     "Use very simple words and short sentences. Avoid jargon. Be very encouraging.",
        "intermediate": "Use moderate vocabulary. Explain grammar terms briefly. Balance challenge with support.",
        "advanced":     "Use precise linguistic terminology. Offer nuanced, detailed explanations. Challenge them.",
    }

    learned = ", ".join([t["topic"] for t in p["learned_topics"]]) or "none yet"
    mastered = ", ".join([t["topic"] for t in p["learned_topics"] if t["mastered"]]) or "none yet"

    return f"""You are an adaptive English grammar tutor. Your job is to teach English in a personalised, encouraging way.

STUDENT PROFILE (update your behaviour based on this):
- Detected level: {p['level']}
- Grammar strength: {p['grammar_score']:.0%} ({'strong' if p['grammar_score'] > 0.65 else 'needs work'})
- Vocabulary strength: {p['vocabulary_score']:.0%} ({'strong' if p['vocabulary_score'] > 0.65 else 'needs work'})
- Topics introduced: {learned}
- Topics mastered: {mastered}

LEVEL GUIDANCE:
{level_guidance.get(p['level'], level_guidance['unknown'])}

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
"""

# ─── Profile Updater (called after each reply) ───────────────────────────────
def update_profile_from_reply(user_sentence: str, tutor_reply: str):
    """Ask the model to extract structured signals about student performance."""
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
        # strip possible markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        signals = json.loads(raw)

        p = st.session_state.student_profile
        p["exchange_count"] += 1

        # Update level (exponential moving average of signals)
        level_map = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0, "unknown": None}
        lv = level_map.get(signals.get("level_signal", "unknown"))
        if lv is not None:
            # After 5+ exchanges, lock level more firmly
            alpha = 0.2 if p["exchange_count"] > 5 else 0.4
            current_lv = level_map.get(p["level"], 0.5) if p["level"] != "unknown" else lv
            blended = (1 - alpha) * current_lv + alpha * lv
            if blended < 0.25:
                p["level"] = "beginner"
            elif blended < 0.75:
                p["level"] = "intermediate"
            else:
                p["level"] = "advanced"

        # Update scores
        smooth = 0.25
        if signals.get("grammar_ok") is True:
            p["grammar_score"] = min(1.0, p["grammar_score"] + smooth * (1 - p["grammar_score"]))
        elif signals.get("grammar_ok") is False:
            p["grammar_score"] = max(0.0, p["grammar_score"] - smooth * p["grammar_score"])

        if signals.get("vocabulary_ok") is True:
            p["vocabulary_score"] = min(1.0, p["vocabulary_score"] + smooth * (1 - p["vocabulary_score"]))
        elif signals.get("vocabulary_ok") is False:
            p["vocabulary_score"] = max(0.0, p["vocabulary_score"] - smooth * p["vocabulary_score"])

        # Track topics
        topic = signals.get("topic_introduced")
        if topic and topic != "null":
            existing = next((t for t in p["learned_topics"] if t["topic"] == topic), None)
            if existing:
                if signals.get("topic_mastered"):
                    existing["mastered"] = True
            else:
                p["learned_topics"].append({"topic": topic, "mastered": bool(signals.get("topic_mastered"))})

    except Exception:
        # Silent fail — profile just won't update this turn
        st.session_state.student_profile["exchange_count"] += 1


# ─── Ask Tutor ───────────────────────────────────────────────────────────────
def ask_tutor(sentence: str) -> str:
    st.session_state.conversation_history.append({"role": "user", "content": sentence})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt()},
            *st.session_state.conversation_history,
        ],
    )
    reply = response.choices[0].message.content
    st.session_state.conversation_history.append({"role": "assistant", "content": reply})
    return reply


def ask_for_review() -> str:
    """Trigger an explicit periodic review message."""
    p = st.session_state.student_profile
    learned = ", ".join([t["topic"] for t in p["learned_topics"]]) or "general English"
    weak = []
    if p["grammar_score"] < 0.5:
        weak.append("grammar")
    if p["vocabulary_score"] < 0.5:
        weak.append("vocabulary")
    weak_str = " and ".join(weak) if weak else "no specific weakness detected"

    review_prompt = (
        f"Please give the student a friendly progress review. "
        f"Topics covered: {learned}. Areas needing more work: {weak_str}. "
        f"End with one short exercise sentence for the student to correct or complete."
    )
    st.session_state.conversation_history.append({"role": "user", "content": "[SYSTEM REVIEW REQUEST]"})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt()},
            *st.session_state.conversation_history[:-1],  # exclude fake user msg
            {"role": "user", "content": review_prompt},
        ],
    )
    reply = response.choices[0].message.content
    # Replace the fake user message with assistant reply in history
    st.session_state.conversation_history[-1] = {"role": "assistant", "content": f"📊 **Progress Review**\n\n{reply}"}
    st.session_state.student_profile["last_review_at"] = st.session_state.student_profile["exchange_count"]
    return f"📊 **Progress Review**\n\n{reply}"


# ─── Sidebar: Student Profile ────────────────────────────────────────────────
with st.sidebar:
    st.header("🧠 Student Profile")
    p = st.session_state.student_profile

    level_emoji = {"beginner": "🌱", "intermediate": "🌿", "advanced": "🌳", "unknown": "❓"}
    st.metric("Level", f"{level_emoji.get(p['level'], '❓')} {p['level'].capitalize()}")

    st.write("**Skill Scores**")
    st.progress(p["grammar_score"], text=f"Grammar: {p['grammar_score']:.0%}")
    st.progress(p["vocabulary_score"], text=f"Vocabulary: {p['vocabulary_score']:.0%}")

    st.write(f"**Exchanges:** {p['exchange_count']}")

    if p["learned_topics"]:
        st.write("**Topics:**")
        for t in p["learned_topics"]:
            icon = "✅" if t["mastered"] else "📖"
            st.write(f"{icon} {t['topic']}")

    st.divider()
    if st.button("🔄 Reset Session"):
        for key in defaults:
            st.session_state[key] = defaults[key] if not isinstance(defaults[key], dict) else defaults[key].copy()
        st.rerun()

# ─── Chat History ─────────────────────────────────────────────────────────────
REVIEW_EVERY = 6  # exchanges between automatic reviews

# Show initial greeting if conversation is empty
if not st.session_state.conversation_history:
    initial_greeting = "Hello! I'm your English grammar tutor. 👋\n\nTo get started, simply type any English sentence — it can be about any topic you'd like. I'll give you friendly feedback, correct any mistakes, and help you improve.\n\nGo ahead, try your first sentence!"
    with st.chat_message("assistant"):
        st.markdown(initial_greeting)
    # Add greeting to history so it persists
    st.session_state.conversation_history.append({"role": "assistant", "content": initial_greeting})

# Skip the first message (initial greeting) since it's already displayed above
for message in st.session_state.conversation_history[1:]:
    if message["content"] == "[SYSTEM REVIEW REQUEST]":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─── Input ────────────────────────────────────────────────────────────────────
if sentence := st.chat_input("Type a sentence for feedback…"):
    with st.chat_message("user"):
        st.write(sentence)

    # Check if a review is due BEFORE this turn
    p = st.session_state.student_profile
    review_due = (
        p["exchange_count"] > 0
        and p["exchange_count"] % REVIEW_EVERY == 0
        and p["exchange_count"] != p["last_review_at"]
    )

    with st.chat_message("assistant"):
        if review_due:
            with st.spinner("Preparing your progress review…"):
                review_reply = ask_for_review()
            st.markdown(review_reply)
            st.divider()

        with st.spinner("Thinking…"):
            reply = ask_tutor(sentence)
            update_profile_from_reply(sentence, reply)
        st.markdown(reply)
import streamlit as st
from tutor import (
    default_state,
    ask_tutor,
    ask_for_review,
    update_profile,
    is_review_due,
    INITIAL_GREETING,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="English Grammar Tutor", page_icon="📚", layout="centered")
st.title("📚 English Grammar Tutor")

# ─── Session State Init ───────────────────────────────────────────────────────
if "conversation_history" not in st.session_state:
    st.session_state.update(default_state())

# ─── Sidebar: Student Profile ─────────────────────────────────────────────────
with st.sidebar:
    st.header("🧠 Student Profile")
    p = st.session_state.student_profile

    level_emoji = {"beginner": "🌱", "intermediate": "🌿", "advanced": "🌳", "unknown": "❓"}
    st.metric("Level", f"{level_emoji.get(p['level'], '❓')} {p['level'].capitalize()}")

    st.write("**Skill Scores**")
    st.progress(p["grammar_score"],    text=f"Grammar: {p['grammar_score']:.0%}")
    st.progress(p["vocabulary_score"], text=f"Vocabulary: {p['vocabulary_score']:.0%}")
    st.write(f"**Exchanges:** {p['exchange_count']}")

    if p["learned_topics"]:
        st.write("**Topics:**")
        for t in p["learned_topics"]:
            icon = "✅" if t["mastered"] else "📖"
            st.write(f"{icon} {t['topic']}")

    st.divider()
    if st.button("🔄 Reset Session"):
        st.session_state.update(default_state())
        st.rerun()

# ─── Initial Greeting ─────────────────────────────────────────────────────────
history = st.session_state.conversation_history

if not history:
    with st.chat_message("assistant"):
        st.markdown(INITIAL_GREETING)
    st.session_state.conversation_history = [{"role": "assistant", "content": INITIAL_GREETING}]
    history = st.session_state.conversation_history

# ─── Chat History ─────────────────────────────────────────────────────────────
for message in history[1:]:  # skip greeting — already rendered above
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─── Input ────────────────────────────────────────────────────────────────────
if sentence := st.chat_input("Type a sentence for feedback…"):
    with st.chat_message("user"):
        st.write(sentence)

    profile = st.session_state.student_profile

    with st.chat_message("assistant"):
        if is_review_due(profile):
            with st.spinner("Preparing your progress review…"):
                review_text, history, profile = ask_for_review(history, profile)
            st.markdown(review_text)
            st.divider()
            st.session_state.conversation_history = history
            st.session_state.student_profile = profile

        with st.spinner("Thinking…"):
            reply, history = ask_tutor(sentence, history, profile)
            profile = update_profile(profile, sentence, reply)

        st.markdown(reply)

    st.session_state.conversation_history = history
    st.session_state.student_profile = profile
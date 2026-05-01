import streamlit as st
from tutor import (
    ask_tutor,
    ask_for_review,
    is_review_due,
    update_profile,
    default_profile,
    INITIAL_GREETING,
)
from db import (
    get_or_create_student,
    load_progress,
    save_progress,
    advance_step,
    get_current_lesson,
    save_message,
    load_message_history,
)

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ella — English Tutor",
    page_icon="📚",
    layout="centered",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main { background-color: #fafaf8; }

.stApp {
    background-color: #fafaf8;
}

/* Header */
.tutor-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
}
.tutor-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #1a1a1a;
    margin-bottom: 0.2rem;
}
.tutor-header p {
    color: #888;
    font-size: 0.95rem;
    font-weight: 300;
}

/* Level badge */
.level-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-left: 6px;
}
.level-unknown      { background: #f0f0ee; color: #888; }
.level-beginner     { background: #e8f4e8; color: #2d7a2d; }
.level-intermediate { background: #fff4e0; color: #b36200; }
.level-advanced     { background: #e8eeff; color: #2a3eb1; }

/* Chat bubbles */
.chat-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.5rem 0;
}
.chat-tutor {
    display: flex;
    justify-content: flex-start;
    margin: 0.5rem 0;
}
.bubble-user {
    background: #1a1a1a;
    color: #fff;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.55;
}
.bubble-tutor {
    background: #fff;
    color: #1a1a1a;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 75%;
    font-size: 0.95rem;
    line-height: 1.55;
    border: 1px solid #ebebeb;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.bubble-review {
    background: #f7f5ff;
    border: 1px solid #ddd8ff;
    color: #1a1a1a;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 80%;
    font-size: 0.95rem;
    line-height: 1.55;
}
.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #e8eeff;
    color: #2a3eb1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
    margin-right: 8px;
    margin-top: 2px;
}

/* Progress bar */
.progress-bar-wrap {
    background: #ebebeb;
    border-radius: 8px;
    height: 6px;
    margin: 4px 0 12px 0;
}
.progress-bar-fill {
    height: 6px;
    border-radius: 8px;
    background: linear-gradient(90deg, #4f46e5, #818cf8);
    transition: width 0.4s ease;
}

/* Stat cards */
.stat-row {
    display: flex;
    gap: 10px;
    margin-bottom: 1rem;
}
.stat-card {
    flex: 1;
    background: #fff;
    border: 1px solid #ebebeb;
    border-radius: 12px;
    padding: 10px 14px;
    text-align: center;
}
.stat-label {
    font-size: 0.7rem;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.stat-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-top: 2px;
}

/* Lesson chip */
.lesson-chip {
    background: #f0f4ff;
    border: 1px solid #d8e0ff;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: #4f46e5;
    margin-bottom: 1rem;
}
.lesson-chip span {
    font-weight: 600;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────

if "student_id"  not in st.session_state: st.session_state.student_id  = None
if "profile"     not in st.session_state: st.session_state.profile     = default_profile()
if "history"     not in st.session_state: st.session_state.history     = []
if "messages"    not in st.session_state: st.session_state.messages    = []
if "progress"    not in st.session_state: st.session_state.progress    = None
if "lesson"      not in st.session_state: st.session_state.lesson      = None
if "name"        not in st.session_state: st.session_state.name        = ""
if "started"     not in st.session_state: st.session_state.started     = False

# ─── Login Screen ─────────────────────────────────────────────────────────────

if not st.session_state.started:
    st.markdown("""
    <div class="tutor-header">
        <h1>Ella</h1>
        <p>Your personal English tutor — adaptive, patient, and always encouraging.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("What's your name?", placeholder="e.g. Maria", label_visibility="visible")
        if st.button("Start Learning →", use_container_width=True) and name.strip():
            with st.spinner("Setting up your session..."):
                student_id = get_or_create_student(name.strip())
                progress   = load_progress(student_id)
                lesson     = get_current_lesson(progress["current_step"])
                history    = load_message_history(student_id)

                st.session_state.student_id = student_id
                st.session_state.name       = name.strip()
                st.session_state.progress   = progress
                st.session_state.lesson     = lesson
                st.session_state.history    = history
                st.session_state.started    = True

                # add greeting as first message if no history
                if not history:
                    st.session_state.messages = [
                        {"role": "assistant", "content": INITIAL_GREETING}
                    ]
                else:
                    st.session_state.messages = history

            st.rerun()
    st.stop()

# ─── Main App ─────────────────────────────────────────────────────────────────

profile  = st.session_state.profile
lesson   = st.session_state.lesson
progress = st.session_state.progress

# Header
level = profile["level"]
level_class = f"level-{level}"
st.markdown(f"""
<div class="tutor-header">
    <h1>Ella <span class="level-badge {level_class}">{level}</span></h1>
    <p>Your adaptive English tutor</p>
</div>
""", unsafe_allow_html=True)

# Sidebar — student stats
with st.sidebar:
    st.markdown(f"### 👋 Hi, {st.session_state.name}!")
    st.markdown("---")

    # grammar score
    g_score = int(profile["grammar_score"] * 100)
    st.markdown(f"**Grammar** — {g_score}%")
    st.markdown(f"""
    <div class="progress-bar-wrap">
        <div class="progress-bar-fill" style="width:{g_score}%"></div>
    </div>
    """, unsafe_allow_html=True)

    # vocab score
    v_score = int(profile["vocabulary_score"] * 100)
    st.markdown(f"**Vocabulary** — {v_score}%")
    st.markdown(f"""
    <div class="progress-bar-wrap">
        <div class="progress-bar-fill" style="width:{v_score}%"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # stats
    exchanges = profile["exchange_count"]
    topics    = len(profile["learned_topics"])
    mastered  = len([t for t in profile["learned_topics"] if t["mastered"]])
    step      = progress["current_step"] if progress else 1

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">Exchanges</div>
            <div class="stat-value">{exchanges}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Topics</div>
            <div class="stat-value">{topics}</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-label">Mastered</div>
            <div class="stat-value">{mastered}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Step</div>
            <div class="stat-value">{step}/981</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # current lesson chip
    if lesson:
        st.markdown(f"""
        <div class="lesson-chip">
            📌 <span>Today's focus</span><br>
            {lesson.get('cefr_level','')}: {lesson.get('guideword','').replace('FORM: ','').replace('USE: ','')}
        </div>
        """, unsafe_allow_html=True)

    # learned topics
    if profile["learned_topics"]:
        st.markdown("**Topics covered:**")
        for t in profile["learned_topics"]:
            icon = "✅" if t["mastered"] else "🔄"
            st.markdown(f"{icon} {t['topic']}")

    st.markdown("---")
    if st.button("End Session", use_container_width=True):
        if progress:
            new_sessions = progress["sessions_on_step"] + 1
            if new_sessions >= 2:
                advance_step(st.session_state.student_id, progress["current_step"])
            else:
                save_progress(st.session_state.student_id, progress["current_step"], new_sessions)
        st.session_state.started = False
        st.session_state.student_id = None
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.profile = default_profile()
        st.rerun()

# ─── Chat Display ─────────────────────────────────────────────────────────────

chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-user">
                <div class="bubble-user">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            is_review = msg["content"].startswith("📊")
            bubble_class = "bubble-review" if is_review else "bubble-tutor"
            st.markdown(f"""
            <div class="chat-tutor">
                <div class="avatar">E</div>
                <div class="{bubble_class}">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Input ────────────────────────────────────────────────────────────────────

user_input = st.chat_input("Type a sentence in English...")

if user_input and user_input.strip():
    # add user message to display
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(st.session_state.student_id, "user", user_input)

    # get AI response
    with st.spinner("Ella is thinking..."):
        if is_review_due(profile):
            reply, new_history, new_profile = ask_for_review(
                st.session_state.history, profile, lesson
            )
            st.session_state.profile = new_profile
        else:
            reply, new_history = ask_tutor(
                user_input, st.session_state.history, profile, lesson
            )

        # update history and profile
        st.session_state.history = new_history
        st.session_state.profile = update_profile(profile, user_input, reply)

    # save and display assistant reply
    save_message(st.session_state.student_id, "assistant", reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    st.rerun()
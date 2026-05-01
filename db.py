from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ─── Student ──────────────────────────────────────────────────────────────────

def get_or_create_student(name: str) -> int:
    """
    Returns student_id. Creates a new student if they don't exist yet.
    """
    # check if student exists
    result = supabase.table("students")\
        .select("id")\
        .eq("name", name)\
        .execute()

    if result.data:
        student_id = result.data[0]["id"]
        print(f"Welcome back, {name}!")
    else:
        # create new student
        new_student = supabase.table("students")\
            .insert({"name": name})\
            .execute()
        student_id = new_student.data[0]["id"]

        # create their progress row starting at step 1
        supabase.table("student_progress").insert({
            "student_id": student_id,
            "current_step": 1,
            "sessions_on_step": 0
        }).execute()

        print(f"Welcome, {name}! Starting from the beginning.")

    return student_id


# ─── Progress ─────────────────────────────────────────────────────────────────

def load_progress(student_id: int) -> dict:
    """
    Returns the student's current progress from the DB.
    """
    result = supabase.table("student_progress")\
        .select("current_step, sessions_on_step")\
        .eq("student_id", student_id)\
        .execute()

    return result.data[0] if result.data else {"current_step": 1, "sessions_on_step": 0}


def save_progress(student_id: int, current_step: int, sessions_on_step: int):
    """
    Updates the student's progress in the DB.
    """
    supabase.table("student_progress").update({
        "current_step": current_step,
        "sessions_on_step": sessions_on_step,
    }).eq("student_id", student_id).execute()


def advance_step(student_id: int, current_step: int):
    """
    Moves student to the next curriculum step.
    """
    supabase.table("student_progress").update({
        "current_step": current_step + 1,
        "sessions_on_step": 0,
    }).eq("student_id", student_id).execute()
    print(f"Advanced to step {current_step + 1}")


# ─── Curriculum ───────────────────────────────────────────────────────────────

def get_current_lesson(current_step: int) -> dict:
    """
    Returns the grammar lesson for the current step.
    """
    result = supabase.table("grammar_lessons")\
        .select("*")\
        .eq("step", current_step)\
        .execute()

    return result.data[0] if result.data else None


# ─── Messages ─────────────────────────────────────────────────────────────────

def save_message(student_id: int, role: str, content: str):
    """
    Saves a single message to the messages table.
    role is either 'user' or 'assistant'
    """
    supabase.table("messages").insert({
        "student_id": student_id,
        "role": role,
        "content": content
    }).execute()


def load_message_history(student_id: int, limit: int = 20) -> list:
    """
    Loads the last N messages for a student.
    Returns them in the format Groq expects.
    """
    result = supabase.table("messages")\
        .select("role, content")\
        .eq("student_id", student_id)\
        .order("created_at", desc=False)\
        .limit(limit)\
        .execute()

    return result.data if result.data else []
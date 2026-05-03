import json
import os
import csv

DB_FILE = "db.json"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"students": {}} 


def _save_db(db: dict):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ─── Student ──────────────────────────────────────────────────────────────────

def get_or_create_student(name: str) -> str:
    db = _load_db()
    if name in db["students"]:
        print(f"Welcome back, {name}!")
    else:
        db["students"][name] = {
            "progress": {"current_step": 1, "sessions_on_step": 0},
            "messages": []
        }
        _save_db(db)
        print(f"Welcome, {name}! Starting from the beginning.")
    return name  

# ─── Progress ─────────────────────────────────────────────────────────────────

def load_progress(student_id: str) -> dict:
    db = _load_db()
    return db["students"][student_id]["progress"]

def save_progress(student_id: str, current_step: int, sessions_on_step: int):
    db = _load_db()
    db["students"][student_id]["progress"] = {
        "current_step": current_step,
        "sessions_on_step": sessions_on_step,
    }
    _save_db(db)

def advance_step(student_id: str, current_step: int):
    db = _load_db()
    db["students"][student_id]["progress"] = {
        "current_step": current_step + 1,
        "sessions_on_step": 0,
    }
    _save_db(db)
    print(f"Advanced to step {current_step + 1}")

# ─── Curriculum ───────────────────────────────────────────────────────────────

def get_current_lesson(current_step: int) -> dict | None:
    with open("grammar_profile_cleaned.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["step"]) == current_step:
                return {
                    "cefr_level":         row["cefr_level"],
                    "guideword":          row["guideword"],
                    "learning_objective": row["learning_objective"],
                    "example_sentence":   row["example_sentence"],
                    "grammar_category":   row["grammar_category"],
                    "sub_category":       row["sub_category"],
                    "lexical_range":      row["lexical_range"],
                }
    return None
# ─── Messages ─────────────────────────────────────────────────────────────────

def save_message(student_id: str, role: str, content: str):
    db = _load_db()
    db["students"][student_id]["messages"].append({
        "role": role,
        "content": content
    })
    _save_db(db)

def load_message_history(student_id: str, limit: int = 20) -> list:
    db = _load_db()
    messages = db["students"][student_id]["messages"]
    return messages[-limit:]
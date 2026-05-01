

-- Grammar-based cirriculum 
CREATE TABLE grammar_lessons (
  id                SERIAL PRIMARY KEY,
  step              INTEGER UNIQUE NOT NULL,   -- global ordering A1→B2
  cefr_level        TEXT NOT NULL,             -- 'A1', 'A2', 'B1', 'B2'
  grammar_category  TEXT NOT NULL,             -- 'ADJECTIVES', 'VERBS', etc.
  sub_category      TEXT,                      -- 'combining', 'comparative', etc.
  guideword         TEXT NOT NULL,             -- specific rule name
  learning_objective TEXT NOT NULL,            -- can-do statement
  example_sentence  TEXT,                      -- real example from Cambridge data
  lexical_range     TEXT                       -- complexity hint (can be null)
);


-- Students
CREATE TABLE students (
  id          SERIAL PRIMARY KEY,
  name        TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);


-- Student progress tracking
CREATE TABLE student_progress (
  id                SERIAL PRIMARY KEY,
  student_id        INTEGER REFERENCES students(id) ON DELETE CASCADE,
  current_step      INTEGER DEFAULT 1,         -- maps to grammar_lessons.step
  sessions_on_step  INTEGER DEFAULT 0,         -- how many sessions at this step
  updated_at        TIMESTAMP DEFAULT NOW(),
  UNIQUE(student_id)
);


-- Message history for each student (for context in conversations)
CREATE TABLE messages (
  id          SERIAL PRIMARY KEY,
  student_id  INTEGER REFERENCES students(id) ON DELETE CASCADE,
  role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content     TEXT NOT NULL,
  created_at  TIMESTAMP DEFAULT NOW()
);


-- Get the current lesson for a student
CREATE OR REPLACE FUNCTION get_current_lesson(p_student_id INT)
RETURNS TABLE (
  step              INT,
  cefr_level        TEXT,
  grammar_category  TEXT,
  sub_category      TEXT,
  guideword         TEXT,
  learning_objective TEXT,
  example_sentence  TEXT
) AS $$
  SELECT
    gl.step,
    gl.cefr_level,
    gl.grammar_category,
    gl.sub_category,
    gl.guideword,
    gl.learning_objective,
    gl.example_sentence
  FROM student_progress sp
  JOIN grammar_lessons gl ON gl.step = sp.current_step
  WHERE sp.student_id = p_student_id;
$$ LANGUAGE sql;


-- Increment session count and auto-advance after 2 sessions
CREATE OR REPLACE FUNCTION increment_session(p_student_id INT)
RETURNS VOID AS $$
  UPDATE student_progress
  SET
    sessions_on_step = CASE
      WHEN sessions_on_step + 1 >= 2 THEN 0
      ELSE sessions_on_step + 1
    END,
    current_step = CASE
      WHEN sessions_on_step + 1 >= 2 THEN current_step + 1
      ELSE current_step
    END,
    updated_at = NOW()
  WHERE student_id = p_student_id;
$$ LANGUAGE sql;


-- Manually advance a student to the next step
CREATE OR REPLACE FUNCTION advance_step(p_student_id INT)
RETURNS VOID AS $$
  UPDATE student_progress
  SET
    current_step     = current_step + 1,
    sessions_on_step = 0,
    updated_at       = NOW()
  WHERE student_id = p_student_id;
$$ LANGUAGE sql;

import json
import os
import re
import sqlite3
from datetime import datetime, date

import streamlit as st
from google import genai

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="wide",
)

DB_PATH = "studymate.db"
MODEL_NAME = "gemini-3.5-flash-lite"


def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def ask_ai(prompt):
    """Return Gemini text, or raise a useful error for the UI to display."""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "Gemini API key is not configured. Add GEMINI_API_KEY to "
            ".streamlit/secrets.toml (keep that file private)."
        )
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    answer = getattr(response, "text", None)
    if not answer:
        raise RuntimeError("The AI returned an empty response. Please try again.")
    return answer.strip()


# ---------------- LOCAL DATABASE ----------------
def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            goal TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


db = connect_db()


def save_score(subject, topic, score, total):
    db.execute(
        "INSERT INTO quiz_scores(created_at, subject, topic, score, total) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), subject, topic, score, total),
    )
    db.commit()


def save_note(subject, topic, content):
    db.execute(
        "INSERT INTO saved_notes(created_at, subject, topic, content) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), subject, topic, content),
    )
    db.commit()


def save_plan(goal, content):
    db.execute(
        "INSERT INTO study_plans(created_at, goal, content) VALUES (?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), goal, content),
    )
    db.commit()


def extract_json(text):
    """Accept clean JSON or JSON wrapped in a Markdown code fence."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The AI response did not contain valid JSON.")
    return json.loads(cleaned[start:end + 1])


# ---------------- STYLE ----------------

st.sidebar.title("📚 StudyMate AI")
st.sidebar.caption("Your personal learning companion")
page = st.sidebar.radio(
    "Choose a feature",
    [
        "🏠 Home",
        "🤖 AI Tutor",
        "📝 Quiz Generator",
        "📖 Smart Notes",
        "📅 Study Planner",
        "📊 Progress Tracker",
    ],
)

subjects = ["Science", "Mathematics", "English", "History", "Geography", "Computer Studies"]

st.title("📚 StudyMate AI")
st.caption("Learn smarter. Practise better. Grow with confidence.")

with st.sidebar:
    st.divider()
    st.caption("AI model: Gemini 3.5 Flash-Lite")
    st.caption("Your notes, plans and scores are stored in this app's local SQLite database.")


# ---------------- HOME ----------------
if page == "🏠 Home":
    st.subheader("Welcome to your learning dashboard!")
    name = st.text_input("What should we call you?", key="home_name")
    if name.strip():
        st.success(f"Welcome, {name.strip()}! Ready to learn something new?")
    scores_count = db.execute("SELECT COUNT(*) FROM quiz_scores").fetchone()[0]
    notes_count = db.execute("SELECT COUNT(*) FROM saved_notes").fetchone()[0]
    plans_count = db.execute("SELECT COUNT(*) FROM study_plans").fetchone()[0]
    a, b, c = st.columns(3)
    a.metric("Quizzes completed", scores_count)
    b.metric("Notes saved", notes_count)
    c.metric("Study plans saved", plans_count)
    st.info("Choose a tool from the sidebar to get started.")
    st.markdown("""
    **What you can do**
    - Ask the AI Tutor to explain a topic in student-friendly language.
    - Generate a five-question multiple-choice quiz and receive a score.
    - Create and save revision notes.
    - Build a weekly study timetable.
    - Review your saved learning progress.
    """)


# ---------------- AI TUTOR ----------------
elif page == "🤖 AI Tutor":
    st.subheader("Ask your personal AI tutor")
    subject = st.selectbox("Subject", subjects, key="tutor_subject")
    topic = st.text_input("Topic (optional)", key="tutor_topic")
    question = st.text_area("What would you like explained?", height=120)
    if st.button("Ask StudyMate", type="primary"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            prompt = f"""
You are StudyMate AI, a careful and encouraging school tutor.
Subject: {subject}
Topic: {topic or "Not specified"}
Student question: {question}

Explain clearly at an appropriate school level. Use headings and a simple
example where useful. If the question is ambiguous, say what you are assuming.
Do not invent facts.
"""
            with st.spinner("StudyMate is thinking..."):
                try:
                    st.markdown(ask_ai(prompt))
                except Exception as exc:
                    st.error(str(exc))


# ---------------- QUIZ ----------------
elif page == "📝 Quiz Generator":
    st.subheader("Create a practice quiz")
    subject = st.selectbox("Subject", subjects, key="quiz_subject")
    topic = st.text_input("Quiz topic", key="quiz_topic_input")
    level = st.selectbox("Difficulty", ["Easy", "Medium", "Challenging"])
    if st.button("Generate 5 questions", type="primary"):
        if not topic.strip():
            st.warning("Enter a topic first.")
        else:
            prompt = f"""
Create exactly five school-level multiple-choice questions.
Subject: {subject}
Topic: {topic}
Difficulty: {level}

Return ONLY valid JSON in this exact structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": 0,
      "explanation": "Brief explanation"
    }}
  ]
}}
The answer must be an integer from 0 to 3 indicating the correct option.
Make all options distinct and ensure there is exactly one correct answer.
"""
            with st.spinner("Creating your quiz..."):
                try:
                    data = extract_json(ask_ai(prompt))
                    questions = data.get("questions", [])
                    valid = (
                        len(questions) == 5
                        and all(
                            isinstance(q.get("question"), str)
                            and isinstance(q.get("options"), list)
                            and len(q["options"]) == 4
                            and isinstance(q.get("answer"), int)
                            and 0 <= q["answer"] < 4
                            for q in questions
                        )
                    )
                    if not valid:
                        raise ValueError("The quiz format was incomplete. Please generate it again.")
                    st.session_state.active_quiz = {
                        "subject": subject,
                        "topic": topic.strip(),
                        "questions": questions,
                    }
                    st.session_state.pop("quiz_submitted", None)
                except Exception as exc:
                    st.error(f"Could not create the quiz: {exc}")

    quiz = st.session_state.get("active_quiz")
    if quiz:
        st.divider()
        st.markdown(f"**{quiz['subject']} · {quiz['topic']}**")
        if not st.session_state.get("quiz_submitted", False):
            with st.form("quiz_form"):
                answers = []
                for i, q in enumerate(quiz["questions"]):
                    st.markdown(f"**{i + 1}. {q['question']}**")
                    choice = st.radio(
                        "Choose one answer",
                        options=range(4),
                        format_func=lambda x, opts=q["options"]: opts[x],
                        key=f"quiz_answer_{i}",
                        index=None,
                    )
                    answers.append(choice)
                submitted = st.form_submit_button("Submit answers", type="primary")
            if submitted:
                if any(answer is None for answer in answers):
                    st.warning("Please answer all five questions before submitting.")
                else:
                    score = sum(
                        answers[i] == q["answer"]
                        for i, q in enumerate(quiz["questions"])
                    )
                    st.session_state.quiz_result = {
                        "answers": answers,
                        "score": score,
                    }
                    st.session_state.quiz_submitted = True
                    save_score(quiz["subject"], quiz["topic"], score, len(quiz["questions"]))
                    st.rerun()
        else:
            result = st.session_state.quiz_result
            score = result["score"]
            st.success(f"You scored {score} out of 5 ({score * 20}%).")
            for i, q in enumerate(quiz["questions"]):
                chosen = result["answers"][i]
                correct = q["answer"]
                if chosen == correct:
                    st.markdown(f"**{i + 1}. Correct!** {q['question']}")
                else:
                    st.markdown(f"**{i + 1}. Not quite.** {q['question']}")
                    st.write(f"Your answer: {q['options'][chosen]}")
                st.write(f"Correct answer: {q['options'][correct]}")
                st.caption(q.get("explanation", ""))
            if st.button("Create another quiz"):
                st.session_state.pop("active_quiz", None)
                st.session_state.pop("quiz_submitted", None)
                st.session_state.pop("quiz_result", None)
                st.rerun()


# ---------------- SMART NOTES ----------------
elif page == "📖 Smart Notes":
    st.subheader("Create revision notes")
    subject = st.selectbox("Subject", subjects, key="notes_subject")
    topic = st.text_input("Chapter or topic", key="notes_topic")
    detail = st.selectbox("Notes length", ["Short", "Medium", "Detailed"])
    if st.button("Generate notes", type="primary"):
        if not topic.strip():
            st.warning("Enter a topic first.")
        else:
            prompt = f"""
Create {detail.lower()} revision notes for a school student.
Subject: {subject}
Topic: {topic}
Use a clear title, short introduction, key points, important definitions,
one example if relevant, and a quick recap. Keep facts accurate.
"""
            with st.spinner("Preparing your notes..."):
                try:
                    notes = ask_ai(prompt)
                    st.session_state.current_notes = {
                        "subject": subject,
                        "topic": topic.strip(),
                        "content": notes,
                    }
                except Exception as exc:
                    st.error(str(exc))
    current = st.session_state.get("current_notes")
    if current:
        st.markdown(current["content"])
        if st.button("Save these notes"):
            save_note(current["subject"], current["topic"], current["content"])
            st.success("Notes saved to your StudyMate database.")


# ---------------- STUDY PLANNER ----------------
elif page == "📅 Study Planner":
    st.subheader("Build a weekly study plan")
    goal = st.text_input("Your learning goal", placeholder="Example: Revise for my science test")
    selected = st.multiselect("Subjects to include", subjects)
    hours = st.slider("Study time per day (hours)", 1, 6, 2)
    commitments = st.text_area("Any fixed commitments or preferred break times? (optional)")
    if st.button("Create my weekly plan", type="primary"):
        if not selected:
            st.warning("Select at least one subject.")
        elif not goal.strip():
            st.warning("Please enter a learning goal.")
        else:
            prompt = f"""
Create a realistic seven-day study timetable for a school student.
Goal: {goal}
Subjects: {", ".join(selected)}
Available study time each day: {hours} hours.
Commitments/preferences: {commitments or "None supplied"}.
Use a table with day, subject/topic, study activity and break/revision.
Keep the workload realistic and include at least one lighter review period.
"""
            with st.spinner("Building your timetable..."):
                try:
                    plan = ask_ai(prompt)
                    st.session_state.current_plan = {"goal": goal.strip(), "content": plan}
                except Exception as exc:
                    st.error(str(exc))
    current_plan = st.session_state.get("current_plan")
    if current_plan:
        st.markdown(current_plan["content"])
        if st.button("Save this study plan"):
            save_plan(current_plan["goal"], current_plan["content"])
            st.success("Study plan saved.")


# ---------------- PROGRESS ----------------
elif page == "📊 Progress Tracker":
    st.subheader("Your learning progress")
    scores = db.execute(
        "SELECT created_at, subject, topic, score, total FROM quiz_scores ORDER BY id DESC"
    ).fetchall()
    notes = db.execute(
        "SELECT created_at, subject, topic FROM saved_notes ORDER BY id DESC"
    ).fetchall()
    plans = db.execute(
        "SELECT created_at, goal FROM study_plans ORDER BY id DESC"
    ).fetchall()

    total_quizzes = len(scores)
    total_correct = sum(row[3] for row in scores)
    total_questions = sum(row[4] for row in scores)
    average = round((total_correct / total_questions) * 100) if total_questions else 0

    a, b, c = st.columns(3)
    a.metric("Quizzes completed", total_quizzes)
    b.metric("Overall accuracy", f"{average}%")
    c.metric("Notes saved", len(notes))

    st.markdown("### Quiz history")
    if scores:
        for created, subject, topic, score, total in scores:
            st.write(f"**{subject} – {topic}:** {score}/{total} · {created[:10]}")
    else:
        st.info("Your quiz results will appear here after your first completed quiz.")

    st.markdown("### Saved notes")
    if notes:
        for created, subject, topic in notes:
            st.write(f"📖 {subject} – {topic} · {created[:10]}")
    else:
        st.caption("No saved notes yet.")

    st.markdown("### Saved study plans")
    if plans:
        for created, goal in plans:
            st.write(f"📅 {goal} · {created[:10]}")
    else:
        st.caption("No saved plans yet.")

st.divider()
st.caption("StudyMate AI · Learn Smarter. Grow Faster. 🚀")

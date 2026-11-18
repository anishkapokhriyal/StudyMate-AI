"""
Integration tests for StudyMate AI.

Keep this file beside app.py and test_app.py.
Run: pytest -v test_integration.py

Uses the isolated temporary database fixture from test_app.py.
The real project database is not modified.
"""

import sqlite3
import pytest

from test_app import app_functions


def test_quiz_score_flows_into_progress_tracker(app_functions):
    """Saving a quiz result makes it available to the progress query."""
    db = app_functions["db"]

    app_functions["save_score"]("Mathematics", "Matrices", 4, 5)

    scores = db.execute(
        "SELECT created_at, subject, topic, score, total "
        "FROM quiz_scores ORDER BY id DESC"
    ).fetchall()

    assert len(scores) == 1
    assert scores[0][1:] == ("Mathematics", "Matrices", 4, 5)


def test_progress_tracker_calculates_overall_accuracy(app_functions):
    """Progress accuracy uses total correct answers / total questions."""
    db = app_functions["db"]

    app_functions["save_score"]("Science", "Light", 4, 5)
    app_functions["save_score"]("Mathematics", "Algebra", 3, 5)

    total_correct = db.execute(
        "SELECT SUM(score) FROM quiz_scores"
    ).fetchone()[0]
    total_questions = db.execute(
        "SELECT SUM(total) FROM quiz_scores"
    ).fetchone()[0]

    accuracy = round((total_correct / total_questions) * 100)

    assert total_correct == 7
    assert total_questions == 10
    assert accuracy == 70


def test_smart_notes_are_retrievable_after_saving(app_functions):
    db = app_functions["db"]

    app_functions["save_note"](
        "Computer Studies", "Python", "Variables store values."
    )

    notes = db.execute(
        "SELECT subject, topic, content FROM saved_notes"
    ).fetchall()

    assert notes == [
        ("Computer Studies", "Python", "Variables store values.")
    ]


def test_study_plan_is_retrievable_after_saving(app_functions):
    db = app_functions["db"]

    app_functions["save_plan"](
        "Prepare for exams", "Monday: revise Mathematics."
    )

    plans = db.execute(
        "SELECT goal, content FROM study_plans"
    ).fetchall()

    assert plans == [
        ("Prepare for exams", "Monday: revise Mathematics.")
    ]


def test_all_three_features_store_data_in_their_tables(app_functions):
    """Quiz, notes and planner records can coexist in the same database."""
    db = app_functions["db"]

    app_functions["save_score"]("English", "Grammar", 5, 5)
    app_functions["save_note"]("Science", "Energy", "Energy is conserved.")
    app_functions["save_plan"]("Weekly revision", "Revise two topics daily.")

    quiz_count = db.execute(
        "SELECT COUNT(*) FROM quiz_scores"
    ).fetchone()[0]
    note_count = db.execute(
        "SELECT COUNT(*) FROM saved_notes"
    ).fetchone()[0]
    plan_count = db.execute(
        "SELECT COUNT(*) FROM study_plans"
    ).fetchone()[0]

    assert (quiz_count, note_count, plan_count) == (1, 1, 1)


def test_saved_records_persist_after_database_reopens(app_functions):
    """Saved records remain available after closing and reopening SQLite."""
    db = app_functions["db"]
    db_path = db.execute("PRAGMA database_list").fetchone()[2]

    app_functions["save_score"]("Science", "Electricity", 4, 5)
    app_functions["save_note"]("Science", "Electricity", "V = IR")
    app_functions["save_plan"]("Revision", "Review Ohm's law.")

    db.close()

    reopened = sqlite3.connect(db_path)
    try:
        quiz_count = reopened.execute(
            "SELECT COUNT(*) FROM quiz_scores"
        ).fetchone()[0]
        note_count = reopened.execute(
            "SELECT COUNT(*) FROM saved_notes"
        ).fetchone()[0]
        plan_count = reopened.execute(
            "SELECT COUNT(*) FROM study_plans"
        ).fetchone()[0]

        assert (quiz_count, note_count, plan_count) == (1, 1, 1)
    finally:
        reopened.close()
        app_functions["db"] = sqlite3.connect(":memory:")

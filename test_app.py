"""
Unit tests for StudyMate AI.

Place this file in the same folder as app.py.
Run with: pytest -v test_app.py

These tests load the real function definitions from app.py without importing
or launching the Streamlit interface. Database tests use temporary databases,
so the project's real studymate.db is not modified.
"""

import ast
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest


APP_FILE = Path(__file__).with_name("app.py")


def load_app_functions(function_names, db_path):
    """Load selected real functions from app.py without running the UI."""
    if not APP_FILE.exists():
        pytest.fail(f"Could not find app.py beside this test file: {APP_FILE}")

    source = APP_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(APP_FILE))

    selected = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in function_names
    ]
    found = {node.name for node in selected}
    missing = set(function_names) - found
    if missing:
        pytest.fail(f"Functions not found in app.py: {sorted(missing)}")

    namespace = {
        "json": json,
        "re": re,
        "sqlite3": sqlite3,
        "datetime": datetime,
        "DB_PATH": str(db_path),
    }
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(APP_FILE), "exec"), namespace)
    return namespace


@pytest.fixture
def app_functions(tmp_path):
    """Provide the actual app functions connected to an isolated test DB."""
    functions = load_app_functions(
        ["connect_db", "extract_json", "save_score", "save_note", "save_plan"],
        tmp_path / "test_studymate.db",
    )
    functions["db"] = functions["connect_db"]()
    yield functions
    functions["db"].close()


# ---------------- JSON EXTRACTION TESTS ----------------

def test_extract_json_from_valid_text(app_functions):
    result = app_functions["extract_json"]('{"status": "success"}')
    assert result == {"status": "success"}


def test_extract_json_from_markdown_code_fence(app_functions):
    response = '```json\n{"questions": [], "count": 0}\n```'
    result = app_functions["extract_json"](response)
    assert result == {"questions": [], "count": 0}


def test_extract_json_rejects_text_without_json(app_functions):
    with pytest.raises(ValueError, match="valid JSON"):
        app_functions["extract_json"]("There is no JSON in this response.")


def test_extract_json_rejects_malformed_json(app_functions):
    with pytest.raises(json.JSONDecodeError):
        app_functions["extract_json"]('{"status": }')


# ---------------- DATABASE TESTS ----------------

def test_database_creates_required_tables(app_functions):
    db = app_functions["db"]
    tables = {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    assert {"quiz_scores", "saved_notes", "study_plans"}.issubset(tables)


def test_save_score_stores_quiz_result(app_functions):
    db = app_functions["db"]
    app_functions["save_score"]("Mathematics", "Matrices", 4, 5)

    row = db.execute(
        "SELECT subject, topic, score, total FROM quiz_scores"
    ).fetchone()

    assert row == ("Mathematics", "Matrices", 4, 5)


def test_save_note_stores_note_content(app_functions):
    db = app_functions["db"]
    app_functions["save_note"](
        "Science", "Electricity", "Ohm's law: V = IR"
    )

    row = db.execute(
        "SELECT subject, topic, content FROM saved_notes"
    ).fetchone()

    assert row == ("Science", "Electricity", "Ohm's law: V = IR")


def test_save_plan_stores_study_plan(app_functions):
    db = app_functions["db"]
    app_functions["save_plan"](
        "Prepare for exams", "Monday: Mathematics revision"
    )

    row = db.execute(
        "SELECT goal, content FROM study_plans"
    ).fetchone()

    assert row == ("Prepare for exams", "Monday: Mathematics revision")


def test_saved_data_remains_after_reopening_database(app_functions, tmp_path):
    db_path = tmp_path / "test_studymate.db"
    db = app_functions["db"]

    app_functions["save_score"]("English", "Grammar", 5, 5)
    db.close()

    reopened_db = sqlite3.connect(db_path)
    try:
        row = reopened_db.execute(
            "SELECT subject, topic, score, total FROM quiz_scores"
        ).fetchone()
        assert row == ("English", "Grammar", 5, 5)
    finally:
        reopened_db.close()
        app_functions["db"] = sqlite3.connect(":memory:")


def test_multiple_records_are_saved(app_functions):
    db = app_functions["db"]

    app_functions["save_score"]("Science", "Light", 4, 5)
    app_functions["save_score"]("Mathematics", "Algebra", 5, 5)

    count = db.execute("SELECT COUNT(*) FROM quiz_scores").fetchone()[0]
    assert count == 2

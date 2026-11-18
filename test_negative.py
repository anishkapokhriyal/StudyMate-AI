"""
Negative and robustness tests for StudyMate AI.
Run: pytest -v test_negative.py
"""

import json
import sqlite3
import pytest

from test_app import app_functions


def test_json_parser_rejects_plain_text(app_functions):
    with pytest.raises(ValueError):
        app_functions["extract_json"]("No structured response here")


def test_json_parser_rejects_broken_json(app_functions):
    with pytest.raises(json.JSONDecodeError):
        app_functions["extract_json"]('{"items": [1, 2, }')


def test_json_parser_rejects_unclosed_object(app_functions):
    with pytest.raises(ValueError):
        app_functions["extract_json"]('{"items": [1, 2]')


def test_database_query_with_sql_like_text_is_stored_as_data(app_functions):
    """Parameterized inserts should store text, not execute it as SQL."""
    db = app_functions["db"]
    unusual_topic = "Math'); DROP TABLE quiz_scores; --"

    app_functions["save_score"]("Mathematics", unusual_topic, 2, 5)

    row = db.execute(
        "SELECT topic FROM quiz_scores"
    ).fetchone()
    table_exists = db.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='quiz_scores'"
    ).fetchone()

    assert row[0] == unusual_topic
    assert table_exists is not None


def test_missing_json_braces_is_rejected(app_functions):
    with pytest.raises(ValueError, match="valid JSON"):
        app_functions["extract_json"]('"answer": 2')

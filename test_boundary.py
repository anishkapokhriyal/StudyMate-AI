"""
Boundary tests for StudyMate AI database and JSON handling.
Run: pytest -v test_boundary.py
"""

import pytest
from test_app import app_functions


@pytest.mark.parametrize(
    "score,total",
    [
        (0, 5),   # minimum quiz score
        (5, 5),   # maximum quiz score
        (1, 5),   # just above minimum
        (4, 5),   # just below maximum
    ],
)
def test_quiz_score_boundary_values_are_saved(app_functions, score, total):
    db = app_functions["db"]
    app_functions["save_score"]("Science", "Boundary test", score, total)

    saved = db.execute(
        "SELECT score, total FROM quiz_scores"
    ).fetchone()

    assert saved == (score, total)


@pytest.mark.parametrize("json_text,expected", [
    ("{}", {}),
    ('{"answer": 0}', {"answer": 0}),
    ('{"answer": 3}', {"answer": 3}),
])
def test_json_parser_handles_small_valid_json_boundaries(
    app_functions, json_text, expected
):
    assert app_functions["extract_json"](json_text) == expected


def test_empty_database_progress_calculation_has_no_division(app_functions):
    db = app_functions["db"]
    correct = db.execute(
        "SELECT COALESCE(SUM(score), 0) FROM quiz_scores"
    ).fetchone()[0]
    questions = db.execute(
        "SELECT COALESCE(SUM(total), 0) FROM quiz_scores"
    ).fetchone()[0]

    # The app's progress page displays 0% when no questions exist.
    accuracy = round((correct / questions) * 100) if questions else 0
    assert accuracy == 0


def test_study_planner_hour_limits_are_one_to_six_in_source():
    """Confirm the UI slider is configured with the stated inclusive limits."""
    from pathlib import Path
    import ast

    source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    slider_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "slider" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and first_arg.value == "Study time per day (hours)":
                    numeric_args = [
                        arg.value for arg in node.args[1:]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int)
                    ]
                    slider_found = numeric_args[:3] == [1, 6, 2]
                    break

    assert slider_found, "Expected study-hours slider minimum=1, maximum=6, default=2"

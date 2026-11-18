"""
Functional UI tests for StudyMate AI.
Run: pytest -v test_functional.py

These tests use Streamlit's AppTest to exercise the real app interface.
They do not call Gemini because they test empty-input validation and navigation.
"""

import pytest

streamlit = pytest.importorskip("streamlit")
pytest.importorskip("google.genai")
from streamlit.testing.v1 import AppTest


def launch_app():
    return AppTest.from_file("app.py").run()


def select_page(at, page):
    at.sidebar.radio[0].set_value(page)
    return at.run()


def warning_contains(at, expected):
    return any(expected in item.value for item in at.warning)


def test_home_page_displays_dashboard():
    at = launch_app()
    assert not at.exception
    assert any("StudyMate AI" in item.value for item in at.title)


def test_ai_tutor_shows_validation_for_empty_question():
    at = select_page(launch_app(), "🤖 AI Tutor")
    at.button[0].click().run()
    assert warning_contains(at, "Please enter a question first.")


def test_quiz_generator_shows_validation_for_empty_topic():
    at = select_page(launch_app(), "📝 Quiz Generator")
    at.button[0].click().run()
    assert warning_contains(at, "Enter a topic first.")


def test_smart_notes_shows_validation_for_empty_topic():
    at = select_page(launch_app(), "📖 Smart Notes")
    at.button[0].click().run()
    assert warning_contains(at, "Enter a topic first.")


def test_study_planner_shows_validation_without_subjects():
    at = select_page(launch_app(), "📅 Study Planner")
    at.button[0].click().run()
    assert warning_contains(at, "Select at least one subject.")


def test_progress_tracker_page_opens():
    at = select_page(launch_app(), "📊 Progress Tracker")
    assert not at.exception
    assert any("Your learning progress" in item.value for item in at.subheader)

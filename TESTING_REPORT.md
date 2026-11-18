# StudyMate AI — Testing Report

## Project details
- Project: StudyMate AI
- Main application: `app.py`
- Test framework: pytest
- UI testing tool: Streamlit AppTest
- Database: SQLite

## Test suite
| Testing category | File | Test coverage |
|---|---|---|
| Unit testing | `test_app.py` | JSON parsing, database setup, score/note/plan saving, persistence |
| Integration testing | `test_integration.py` | Saved records retrieved by progress-style queries; combined database workflows |
| Functional testing | `test_functional.py` | Home page, navigation, input validation, Progress Tracker |
| Negative testing | `test_negative.py` | Invalid JSON, malformed input, SQL-like text safety |
| Boundary testing | `test_boundary.py` | Minimum/maximum quiz scores, JSON edge cases, empty progress, study-hours slider limits |

## How to run all tests
Run these commands from the folder containing all the files:

```bash
pip install pytest streamlit google-genai
pytest -v
```

To create a machine-readable test report:

```bash
pytest -v --junitxml=testing-results.xml
```

## Test execution record
Fill this section using the actual output from your computer. Do not mark tests as passed unless pytest reports them as passed.

| Category | Passed | Failed | Skipped |
|---|---:|---:|---:|
| Unit | 10 | 0 | 0 |
| Integration | 6 | 0 | 0 |
| Functional | 0 | 0 | 6* |
| Negative | 5 | 0 | 0 |
| Boundary | 9 | 0 | 0 |
| **Total** | **30** | **0** | **6*** |

*Functional UI tests were skipped in this execution environment because Streamlit and `google-genai` are not installed. Install the dependencies and rerun to execute those six UI tests. The pytest summary from this run was **30 passed, 1 skipped** (the skipped item is the functional test module; its six test cases were not executed).

## Defect log
For each failure, record:
1. Test ID and category.
2. Actual result and expected result.
3. Steps to reproduce.
4. Root cause.
5. Code change made.
6. Retest result.

## Important limitations
- Functional UI tests require Streamlit and the Google GenAI Python package to be installed.
- The functional tests focus on navigation and validation; they do not verify live Gemini response quality.
- The integration tests exercise database workflows using a temporary test database. They do not simulate every browser interaction.
- Passing automated tests is evidence of tested behavior, not proof that the application is defect-free.
- Keep API keys and `.streamlit/secrets.toml` private. Never include them in screenshots or submitted reports.

## Evidence to capture
- Terminal output for `pytest -v`.
- JUnit XML report (`testing-results.xml`).
- Screenshots of each app page working.
- Screenshots or notes showing any defects found, fixes made, and successful retests.

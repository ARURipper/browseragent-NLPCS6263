"""User story acceptance tests — one test per story in docs/STORIES.md."""

import json
from unittest.mock import MagicMock, patch

import pytest

from browseragent.app import app as flask_app
from browseragent.evaluator import evaluate_batch, token_f1


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── US-01: Submit a Question and Receive an Answer ────────────────────────────

@pytest.mark.user_story("US-01")
def test_us01_submit_question_receive_answer(client):
    """
    Given the application is running,
    When I POST a question to /api/ask,
    Then I receive a JSON response with a non-empty answer.
    """
    with patch("browseragent.app.BrowserAgent") as mock_cls:
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.question = "Who directed Schindler's List?"
        mock_result.answer = "Steven Spielberg"
        mock_result.total_steps = 3
        mock_result.success = True
        mock_result.elapsed_seconds = 8.2
        mock_agent.run.return_value = mock_result
        mock_cls.return_value = mock_agent

        resp = client.post(
            "/api/ask",
            data=json.dumps({"question": "Who directed Schindler's List?"}),
            content_type="application/json",
        )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert len(data["answer"]) > 0


# ── US-02: Live Streaming of Browsing Steps ───────────────────────────────────

@pytest.mark.user_story("US-02")
@patch("browseragent.app._run_agent")
@patch("browseragent.app.threading.Thread")
def test_us02_session_page_exists(mock_thread, mock_run, client):
    """
    Given a question is submitted,
    When I visit the session page,
    Then it returns 200 with step-streaming HTML.
    """
    from browseragent.app import _sessions

    mock_thread.return_value = MagicMock()
    resp = client.post("/ask", data={"question": "What is the Eiffel Tower?"})
    assert resp.status_code == 302
    location = resp.headers["Location"]
    session_id = location.rstrip("/").split("/")[-1]

    # Pre-populate session so session page renders
    _sessions[session_id] = {
        "question": "What is the Eiffel Tower?",
        "status": "running",
        "steps": [],
        "answer": "",
    }

    page_resp = client.get(f"/session/{session_id}")
    assert page_resp.status_code == 200
    assert b"EventSource" in page_resp.data  # SSE client present


# ── US-03: JSON REST API ───────────────────────────────────────────────────────

@pytest.mark.user_story("US-03")
def test_us03_json_api_response_schema(client):
    """
    Given a valid POST /api/ask request,
    When the agent answers successfully,
    Then the response JSON contains required keys.
    """
    with patch("browseragent.app.BrowserAgent") as mock_cls:
        mock_result = MagicMock()
        mock_result.question = "test"
        mock_result.answer = "France"
        mock_result.total_steps = 2
        mock_result.success = True
        mock_result.elapsed_seconds = 3.0
        mock_cls.return_value.run.return_value = mock_result

        resp = client.post(
            "/api/ask",
            data=json.dumps({"question": "Where is Eiffel Tower?", "max_steps": 4}),
            content_type="application/json",
        )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    for key in ("question", "answer", "steps", "success", "elapsed_seconds", "request_id"):
        assert key in data, f"Missing key: {key}"


# ── US-04: Health Check Endpoint ──────────────────────────────────────────────

@pytest.mark.user_story("US-04")
def test_us04_health_check(client):
    """
    Given the app is running,
    When GET /health is called,
    Then 200 is returned with status=ok.
    """
    resp = client.get("/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "ok"
    assert data["service"] == "browseragent"


# ── US-05: Error — Empty Question ─────────────────────────────────────────────

@pytest.mark.user_story("US-05")
def test_us05_empty_question_no_crash(client):
    """
    Given the landing page,
    When an empty question is submitted,
    Then the app redirects gracefully (no 500).
    """
    resp = client.post("/ask", data={"question": ""})
    assert resp.status_code in (200, 302)
    assert resp.status_code != 500


# ── US-06: Error — Invalid API Request ────────────────────────────────────────

@pytest.mark.user_story("US-06")
def test_us06_api_missing_question_400(client):
    """
    Given POST /api/ask with empty body,
    When the request is processed,
    Then 400 is returned with error message.
    """
    resp = client.post(
        "/api/ask",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data.get("error") == "question is required"


# ── US-07: Request Tracing via Logs ───────────────────────────────────────────

@pytest.mark.user_story("US-07")
def test_us07_request_id_in_response(client):
    """
    Given a valid API request,
    When the response is received,
    Then it contains a non-empty request_id for log tracing.
    """
    with patch("browseragent.app.BrowserAgent") as mock_cls:
        mock_result = MagicMock()
        mock_result.question = "test"
        mock_result.answer = "Paris"
        mock_result.total_steps = 1
        mock_result.success = True
        mock_result.elapsed_seconds = 1.0
        mock_cls.return_value.run.return_value = mock_result

        resp = client.post(
            "/api/ask",
            data=json.dumps({"question": "Capital of France?"}),
            content_type="application/json",
        )
    data = json.loads(resp.data)
    assert "request_id" in data
    assert len(data["request_id"]) == 8

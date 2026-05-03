"""Unit tests for Flask app routes using test client (no real browser)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from browseragent.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


class TestHealthRoute:
    @pytest.mark.unit
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.unit
    def test_health_json(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert data["service"] == "browseragent"


class TestIndexRoute:
    @pytest.mark.unit
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    @pytest.mark.unit
    def test_index_contains_form(self, client):
        resp = client.get("/")
        assert b"action=\"/ask\"" in resp.data or b'action="/ask"' in resp.data


class TestAskRoute:
    @pytest.mark.unit
    def test_empty_question_redirects(self, client):
        resp = client.post("/ask", data={"question": ""})
        assert resp.status_code == 302

    @pytest.mark.unit
    def test_whitespace_question_redirects(self, client):
        resp = client.post("/ask", data={"question": "   "})
        assert resp.status_code == 302

    @pytest.mark.unit
    @patch("browseragent.app._run_agent")
    @patch("browseragent.app.threading.Thread")
    def test_valid_question_redirects_to_session(self, mock_thread, mock_run, client):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        resp = client.post("/ask", data={"question": "Who invented the telephone?"})
        assert resp.status_code == 302
        assert "/session/" in resp.headers["Location"]


class TestApiAskRoute:
    @pytest.mark.unit
    def test_missing_question_returns_400(self, client):
        resp = client.post(
            "/api/ask",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data
        assert data["error"] == "question is required"

    @pytest.mark.unit
    @patch("browseragent.app.BrowserAgent")
    def test_valid_question_returns_200(self, mock_agent_cls, client):
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.question = "What is 2+2?"
        mock_result.answer = "4"
        mock_result.steps = []
        mock_result.total_steps = 2
        mock_result.success = True
        mock_result.elapsed_seconds = 1.5
        mock_agent.run.return_value = mock_result
        mock_agent_cls.return_value = mock_agent

        resp = client.post(
            "/api/ask",
            data=json.dumps({"question": "What is 2+2?", "max_steps": 3}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["answer"] == "4"
        assert "request_id" in data

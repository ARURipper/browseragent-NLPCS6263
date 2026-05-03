"""Edge case tests: empty, very long, non-ASCII, multilingual, code-mixed, adversarial."""

import json
import string

import pytest

from browseragent.evaluator import exact_match, token_f1


# ─────────────────────────────────────────────────── evaluator edge cases ────

class TestEvaluatorEdgeCases:
    @pytest.mark.edge
    def test_very_long_prediction(self):
        long_pred = " ".join(["word"] * 1000)
        score = token_f1(long_pred, "word")
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_non_ascii_prediction(self):
        # Arabic text
        score = token_f1("باريس", "Paris")
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_chinese_prediction(self):
        score = token_f1("法国", "France")
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_emoji_in_answer(self):
        score = token_f1("Paris 🗼", "Paris")
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_all_punctuation(self):
        score = token_f1(string.punctuation, "answer")
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_numbers_as_answers(self):
        assert token_f1("42", "42") == 1.0

    @pytest.mark.edge
    def test_mixed_language(self):
        # Code-mixed input
        score = token_f1("Paris capitale de France", "Paris")
        assert score > 0.0

    @pytest.mark.edge
    def test_very_long_gold(self):
        long_gold = " ".join(["answer"] * 500)
        score = token_f1("answer", long_gold)
        assert 0.0 <= score <= 1.0

    @pytest.mark.edge
    def test_repeated_words(self):
        # "France France France" vs "France": set overlap gives partial F1
        score = token_f1("France France France", "France")
        assert score > 0.0  # some overlap

    @pytest.mark.edge
    def test_adversarial_similar_words(self):
        # "Paris" vs "Parish" should not be identical
        assert not exact_match("Paris", "Parish")
        score = token_f1("Paris", "Parish")
        assert score < 1.0


# ─────────────────────────────────────────────────── app edge cases ────────────

class TestAppEdgeCases:
    """Test Flask app with edge-case inputs (uses test client, no real browser)."""

    @pytest.fixture(autouse=True)
    def _client(self):
        from browseragent.app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            self.client = c

    @pytest.mark.edge
    def test_empty_string_question_api(self):
        resp = self.client.post(
            "/api/ask",
            data=json.dumps({"question": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @pytest.mark.edge
    def test_very_long_question_api(self):
        """A very long question should not crash the app (returns 200 or 400)."""
        from unittest.mock import MagicMock, patch

        long_q = "What is " + ("foo bar baz " * 200)
        with patch("browseragent.app.BrowserAgent") as mock_cls:
            mock_result = MagicMock()
            mock_result.question = long_q
            mock_result.answer = "unknown"
            mock_result.total_steps = 1
            mock_result.success = False
            mock_result.elapsed_seconds = 0.5
            mock_cls.return_value.run.return_value = mock_result

            resp = self.client.post(
                "/api/ask",
                data=json.dumps({"question": long_q}),
                content_type="application/json",
            )
        assert resp.status_code in (200, 400)

    @pytest.mark.edge
    def test_non_ascii_question_api(self):
        """Non-ASCII questions should not crash the API."""
        from unittest.mock import MagicMock, patch

        with patch("browseragent.app.BrowserAgent") as mock_cls:
            mock_result = MagicMock()
            mock_result.question = "Quel est la capitale de la France?"
            mock_result.answer = "Paris"
            mock_result.total_steps = 1
            mock_result.success = True
            mock_result.elapsed_seconds = 2.0
            mock_cls.return_value.run.return_value = mock_result

            resp = self.client.post(
                "/api/ask",
                data=json.dumps({"question": "Quel est la capitale de la France?"}),
                content_type="application/json",
            )
        assert resp.status_code == 200

    @pytest.mark.edge
    def test_session_not_found_returns_404(self):
        resp = self.client.get("/session/notexist")
        assert resp.status_code == 404

    @pytest.mark.edge
    def test_stream_not_found_returns_404(self):
        resp = self.client.get("/stream/notexist")
        assert resp.status_code == 404

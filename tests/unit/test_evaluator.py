"""Unit tests for browseragent.evaluator and browseragent.logging_config."""

import pytest

from browseragent.evaluator import evaluate_batch, exact_match, token_f1
from browseragent.logging_config import new_request_id, request_id_var, set_request_id


# ─────────────────────────────────────────────────────── evaluator tests ─────

class TestTokenF1:
    @pytest.mark.unit
    def test_identical(self):
        assert token_f1("Paris", "Paris") == 1.0

    @pytest.mark.unit
    def test_complete_mismatch(self):
        assert token_f1("London", "Paris") == 0.0

    @pytest.mark.unit
    def test_partial_overlap(self):
        score = token_f1("Kate Capshaw actress", "Kate Capshaw")
        assert 0 < score < 1.0

    @pytest.mark.unit
    def test_empty_prediction(self):
        assert token_f1("", "Paris") == 0.0

    @pytest.mark.unit
    def test_empty_gold(self):
        assert token_f1("Paris", "") == 0.0

    @pytest.mark.unit
    def test_both_empty(self):
        assert token_f1("", "") == 1.0

    @pytest.mark.unit
    def test_case_insensitive(self):
        assert token_f1("PARIS", "paris") == 1.0

    @pytest.mark.unit
    def test_punctuation_stripped(self):
        assert token_f1("Paris.", "Paris") == 1.0


class TestExactMatch:
    @pytest.mark.unit
    def test_exact(self):
        assert exact_match("France", "France") is True

    @pytest.mark.unit
    def test_case_insensitive(self):
        assert exact_match("france", "France") is True

    @pytest.mark.unit
    def test_punctuation(self):
        assert exact_match("France.", "France") is True

    @pytest.mark.unit
    def test_different(self):
        assert exact_match("Germany", "France") is False


class TestEvaluateBatch:
    @pytest.mark.unit
    def test_basic_batch(self):
        preds = ["Paris", "France", "wrong"]
        golds = ["Paris", "France", "London"]
        result = evaluate_batch(preds, golds)
        assert result["num_samples"] == 3
        assert result["mean_f1"] > 0.5
        assert "accuracy_at_threshold" in result

    @pytest.mark.unit
    def test_length_mismatch_raises(self):
        with pytest.raises(AssertionError):
            evaluate_batch(["a", "b"], ["c"])

    @pytest.mark.unit
    def test_all_correct(self):
        preds = ["Paris", "Berlin"]
        golds = ["Paris", "Berlin"]
        result = evaluate_batch(preds, golds)
        assert result["mean_f1"] == 1.0
        assert result["exact_match"] == 1.0


# ─────────────────────────────────────────────────── logging tests ────────────

class TestLogging:
    @pytest.mark.unit
    def test_new_request_id_format(self):
        rid = new_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 8

    @pytest.mark.unit
    def test_request_id_in_context(self):
        rid = new_request_id()
        assert request_id_var.get() == rid

    @pytest.mark.unit
    def test_set_request_id(self):
        set_request_id("deadbeef")
        assert request_id_var.get() == "deadbeef"

    @pytest.mark.unit
    def test_unique_ids(self):
        id1 = new_request_id()
        id2 = new_request_id()
        assert id1 != id2

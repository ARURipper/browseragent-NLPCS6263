"""Answer evaluator: computes string-overlap F1 between predicted and gold answers."""

from __future__ import annotations

import re
import string
from typing import List

from .logging_config import get_logger

logger = get_logger(__name__)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def token_f1(prediction: str, gold: str) -> float:
    """Token-level F1 between prediction and gold (Squad-style)."""
    pred_tokens = _normalize(prediction).split()
    gold_tokens = _normalize(gold).split()
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = set(pred_tokens) & set(gold_tokens)
    num_common = sum(
        min(pred_tokens.count(t), gold_tokens.count(t)) for t in common
    )
    if num_common == 0:
        return 0.0
    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, gold: str) -> bool:
    """Case-insensitive, punctuation-stripped exact match."""
    return _normalize(prediction) == _normalize(gold)


def evaluate_batch(
    predictions: List[str], golds: List[str], threshold: float = 0.5
) -> dict:
    """Compute aggregate metrics over a list of (pred, gold) pairs."""
    assert len(predictions) == len(golds), "Length mismatch"
    f1_scores = [token_f1(p, g) for p, g in zip(predictions, golds)]
    em_scores = [int(exact_match(p, g)) for p, g in zip(predictions, golds)]
    accuracy = sum(f1 >= threshold for f1 in f1_scores) / len(f1_scores)
    result = {
        "num_samples": len(predictions),
        "mean_f1": sum(f1_scores) / len(f1_scores),
        "exact_match": sum(em_scores) / len(em_scores),
        "accuracy_at_threshold": accuracy,
        "threshold": threshold,
    }
    logger.info("evaluate_batch result=%s", result)
    return result

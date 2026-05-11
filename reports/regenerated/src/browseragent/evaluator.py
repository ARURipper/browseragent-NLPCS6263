"""Token-F1 and exact-match scoring against gold answers."""

import re
import string
from typing import List


def _normalize(text: str) -> str:
    """Normalize text by lowercasing and removing punctuation."""
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def _tokenize(text: str) -> List[str]:
    """Tokenize normalized text into words."""
    normalized = _normalize(text)
    if not normalized:
        return []
    return normalized.split()


def token_f1(prediction: str, gold: str) -> float:
    """
    Token-level F1 between prediction and gold (SQuAD-style).
    
    Args:
        prediction: The predicted answer string
        gold: The gold/reference answer string
        
    Returns:
        F1 score in range [0, 1]
    """
    pred_tokens = _tokenize(prediction)
    gold_tokens = _tokenize(gold)
    
    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0
    
    # Count common tokens
    pred_set = set(pred_tokens)
    gold_set = set(gold_tokens)
    common = pred_set & gold_set
    
    if not common:
        return 0.0
    
    # Calculate precision and recall
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    
    # Calculate F1
    f1 = 2 * precision * recall / (precision + recall)
    return f1


def exact_match(prediction: str, gold: str) -> bool:
    """
    Case-insensitive, punctuation-stripped exact match.
    
    Args:
        prediction: The predicted answer string
        gold: The gold/reference answer string
        
    Returns:
        True if normalized strings match exactly
    """
    return _normalize(prediction) == _normalize(gold)


def evaluate_batch(
    predictions: List[str], golds: List[str], threshold: float = 0.5
) -> dict:
    """
    Evaluate a batch of predictions against gold answers.
    
    Args:
        predictions: List of predicted answer strings
        golds: List of gold/reference answer strings
        threshold: F1 threshold for accuracy calculation
        
    Returns:
        Dictionary with evaluation metrics:
        - num_samples: Number of samples evaluated
        - mean_f1: Mean token F1 score
        - exact_match: Proportion of exact matches
        - accuracy_at_threshold: Proportion with F1 >= threshold
        - threshold: The threshold used
    """
    if len(predictions) != len(golds):
        raise ValueError("predictions and golds must have same length")
    
    num_samples = len(predictions)
    if num_samples == 0:
        return {
            "num_samples": 0,
            "mean_f1": 0.0,
            "exact_match": 0.0,
            "accuracy_at_threshold": 0.0,
            "threshold": threshold,
        }
    
    f1_scores = []
    exact_matches = 0
    above_threshold = 0
    
    for pred, gold in zip(predictions, golds):
        f1 = token_f1(pred, gold)
        f1_scores.append(f1)
        
        if exact_match(pred, gold):
            exact_matches += 1
        
        if f1 >= threshold:
            above_threshold += 1
    
    return {
        "num_samples": num_samples,
        "mean_f1": sum(f1_scores) / num_samples,
        "exact_match": exact_matches / num_samples,
        "accuracy_at_threshold": above_threshold / num_samples,
        "threshold": threshold,
    }

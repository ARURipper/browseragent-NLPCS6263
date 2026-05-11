"""BrowserAgent - A web agent that answers questions by browsing Wikipedia."""

from .agent import BrowserAgent, AgentConfig, AgentResult
from .browser import BrowserSession
from .evaluator import token_f1, exact_match, evaluate_batch
from .logging_config import setup_logging, get_request_id, set_request_id

__all__ = [
    "BrowserAgent",
    "AgentConfig", 
    "AgentResult",
    "BrowserSession",
    "token_f1",
    "exact_match",
    "evaluate_batch",
    "setup_logging",
    "get_request_id",
    "set_request_id",
]

"""Integration tests for the agent pipeline with mocked LLM and browser."""

import json
from unittest.mock import MagicMock, patch

import pytest

from browseragent.agent import AgentConfig, AgentResult, BrowserAgent


def _make_mock_response(action: str, args: dict, reasoning: str = "test") -> MagicMock:
    content = json.dumps({
        "reasoning": reasoning,
        "action": action,
        "args": args,
        "memory_update": f"found info via {action}",
    })
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content=content))]
    return resp


@pytest.fixture
def mock_browser():
    with patch("browseragent.agent.BrowserSession") as cls:
        instance = MagicMock()
        instance.current_url.return_value = "https://en.wikipedia.org/wiki/France"
        instance._extract_text.return_value = "France is a country in Western Europe."
        instance.search_wikipedia.return_value = "France is a country..."
        instance.goto.return_value = "France page text..."
        instance.scroll.return_value = "More text..."
        cls.return_value = instance
        yield instance


@pytest.fixture
def mock_client():
    with patch("browseragent.agent.OpenAI") as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


class TestAgentPipeline:
    @pytest.mark.integration
    def test_stop_on_first_step(self, mock_browser, mock_client):
        mock_client.chat.completions.create.return_value = _make_mock_response(
            "stop", {"answer": "France"}, reasoning="already known"
        )
        config = AgentConfig(max_steps=5, headless=True)
        agent = BrowserAgent(config)
        result = agent.run("What country is Paris in?")
        assert isinstance(result, AgentResult)
        assert result.answer == "France"
        assert result.success is True
        assert result.total_steps == 1

    @pytest.mark.integration
    def test_search_then_stop(self, mock_browser, mock_client):
        mock_client.chat.completions.create.side_effect = [
            _make_mock_response("search", {"query": "Paris capital"}, "looking up Paris"),
            _make_mock_response("stop", {"answer": "France"}, "found answer"),
        ]
        config = AgentConfig(max_steps=5, headless=True)
        agent = BrowserAgent(config)
        result = agent.run("What country is Paris the capital of?")
        assert result.answer == "France"
        assert result.total_steps == 2

    @pytest.mark.integration
    def test_max_steps_respected(self, mock_browser, mock_client):
        mock_client.chat.completions.create.return_value = _make_mock_response(
            "scroll", {"direction": "down"}, "keep scrolling"
        )
        config = AgentConfig(max_steps=3, headless=True)
        agent = BrowserAgent(config)
        result = agent.run("Endless question")
        assert result.total_steps == 3
        assert result.success is False

    @pytest.mark.integration
    def test_stream_yields_steps(self, mock_browser, mock_client):
        mock_client.chat.completions.create.side_effect = [
            _make_mock_response("search", {"query": "test"}, "searching"),
            _make_mock_response("stop", {"answer": "42"}, "done"),
        ]
        config = AgentConfig(max_steps=5, headless=True)
        agent = BrowserAgent(config)
        steps = list(agent.stream("What is the answer?"))
        assert len(steps) == 2
        assert steps[-1]["action"] == "stop"
        assert steps[-1]["answer"] == "42"

    @pytest.mark.integration
    def test_memory_accumulates(self, mock_browser, mock_client):
        mock_client.chat.completions.create.side_effect = [
            _make_mock_response("search", {"query": "foo"}, "step1"),
            _make_mock_response("goto", {"url": "https://en.wikipedia.org/wiki/Foo"}, "step2"),
            _make_mock_response("stop", {"answer": "bar"}, "step3"),
        ]
        config = AgentConfig(max_steps=5, headless=True)
        agent = BrowserAgent(config)
        steps = list(agent.stream("What is foo?"))
        assert len(steps) == 3

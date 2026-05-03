"""Unit tests for agent._parse_action and AgentConfig."""

import json

import pytest

from browseragent.agent import AgentConfig, _parse_action


class TestParseAction:
    @pytest.mark.unit
    def test_clean_json(self):
        raw = json.dumps({
            "reasoning": "test",
            "action": "search",
            "args": {"query": "Eiffel Tower"},
            "memory_update": "",
        })
        result = _parse_action(raw)
        assert result["action"] == "search"
        assert result["args"]["query"] == "Eiffel Tower"

    @pytest.mark.unit
    def test_markdown_fences_stripped(self):
        raw = '```json\n{"action":"stop","args":{"answer":"Paris"},"reasoning":"done","memory_update":""}\n```'
        result = _parse_action(raw)
        assert result["action"] == "stop"
        assert result["args"]["answer"] == "Paris"

    @pytest.mark.unit
    def test_embedded_json_extracted(self):
        raw = 'Here is my response: {"action":"scroll","args":{"direction":"down"},"reasoning":"need more","memory_update":""}'
        result = _parse_action(raw)
        assert result["action"] == "scroll"

    @pytest.mark.unit
    def test_invalid_raises(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            _parse_action("This is not JSON at all")

    @pytest.mark.unit
    def test_goto_action(self):
        raw = json.dumps({
            "reasoning": "follow link",
            "action": "goto",
            "args": {"url": "https://en.wikipedia.org/wiki/France"},
            "memory_update": "France is in Europe",
        })
        result = _parse_action(raw)
        assert result["action"] == "goto"
        assert "wikipedia" in result["args"]["url"]


class TestAgentConfig:
    @pytest.mark.unit
    def test_defaults(self):
        cfg = AgentConfig()
        assert cfg.model == "gpt-4o-mini"
        assert cfg.max_steps == 10
        assert cfg.temperature == 0.0
        assert cfg.headless is True

    @pytest.mark.unit
    def test_custom_config(self):
        cfg = AgentConfig(max_steps=5, temperature=0.5)
        assert cfg.max_steps == 5
        assert cfg.temperature == 0.5

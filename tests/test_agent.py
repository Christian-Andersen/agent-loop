"""Tests for agent factory."""

from __future__ import annotations

from agent_loop.agent import create_agent
from agent_loop.config import AgentDeps
from agent_loop.settings import Settings


class TestCreateAgent:
    """Tests for create_agent."""

    def test_returns_agent(self) -> None:
        """Should return a configured Agent instance."""
        settings = Settings()
        agent = create_agent(settings)
        assert agent is not None
        assert agent.deps_type is AgentDeps

    def test_has_tools(self) -> None:
        """Should register all tools."""
        settings = Settings()
        agent = create_agent(settings)
        names = set(agent._function_toolset.tools)
        expected = {
            "call_opencode",
            "clone_repository",
            "create_branch",
            "commit_changes",
            "show_status",
            "read_todo_file",
            "mark_todo_done",
        }
        assert names == expected

    def test_accepts_modes(self) -> None:
        """Should create agents for all modes."""
        settings = Settings()
        for mode in ("orchestrate", "loop"):
            agent = create_agent(settings, mode=mode)
            assert agent is not None
            assert "call_opencode" in agent._function_toolset.tools

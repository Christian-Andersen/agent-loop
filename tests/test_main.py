"""Tests for CLI entry point."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from agent_loop.main import main


class MainTest:
    """Tests for main()."""

    @patch("agent_loop.main.load_settings")
    def test_loop_no_tasks(self, mock_settings: MagicMock) -> None:
        """Loop with no pending tasks should exit cleanly without checking vLLM."""
        todo = Path("tests") / "fixtures" / "all_done.md"
        with patch("sys.argv", ["agent-loop", "loop", "--todo", str(todo)]):
            main()
        mock_settings.assert_called_once()

    @patch("agent_loop.main._check_vllm")
    @patch("agent_loop.main.create_agent")
    @patch("agent_loop.main.load_settings")
    def test_orchestrate_creates_agent(
        self, mock_settings: MagicMock, mock_create: MagicMock, mock_check: MagicMock
    ) -> None:
        """Orchestrate command should check vLLM and create an agent."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=MagicMock(output="done"))
        mock_create.return_value = mock_agent

        todo = Path("tests") / "fixtures" / "all_done.md"
        with patch("sys.argv", ["agent-loop", "orchestrate", "--todo", str(todo)]):
            main()
        mock_settings.assert_called_once()
        mock_check.assert_called_once()
        mock_create.assert_called_once()

"""Tests for CLI entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_loop.main import main


class MainTest:
    """Tests for main()."""

    @patch("agent_loop.main.load_settings")
    @patch("agent_loop.main.build_bot")
    def test_chat_starts_bot(self, mock_bot: MagicMock) -> None:
        """Chat command should start the Telegram bot."""
        mock_bot.return_value.run_polling = MagicMock()

        with patch("sys.argv", ["agent-loop", "chat"]):
            main()

        mock_bot.assert_called_once()
        mock_bot.return_value.run_polling.assert_called_once()

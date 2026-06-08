"""Tests for Telegram bot handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_loop.settings import Settings
from agent_loop.telegram_bot import handle_message, start_command


@pytest.mark.asyncio
async def test_start_replies() -> None:
    """Should reply to /start."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    await start_command(update, context)
    update.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_skips_no_message() -> None:
    """Should skip when no message."""
    update = MagicMock()
    update.message = None
    context = MagicMock()
    await start_command(update, context)
    # Function returned early without error


@pytest.mark.asyncio
async def test_handle_message_starts_session() -> None:
    """Should start a session for a text message."""
    settings = Settings()

    update = MagicMock()
    update.message = MagicMock()
    update.message.text = "Build something. Repo: git@example.com/test.git"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.application.bot_data = {"settings": settings}
    context.user_data = {}

    with patch("agent_loop.telegram_bot.create_agent") as mock_create:
        mock_agent = AsyncMock()
        mock_agent.run.return_value = MagicMock(output="planned")
        mock_create.return_value = mock_agent

        await handle_message(update, context)

    assert context.user_data.get("active") is True
    update.message.reply_text.assert_awaited()


@pytest.mark.asyncio
async def test_handle_message_skips_no_text() -> None:
    """Should skip messages without text."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = None
    context = MagicMock()
    await handle_message(update, context)
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_active_session_queues() -> None:
    """Should queue input for active sessions."""
    settings = Settings()

    update = MagicMock()
    update.message = MagicMock()
    update.message.text = "add tests"
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.application.bot_data = {"settings": settings}
    context.user_data = {"active": True, "history": []}

    await handle_message(update, context)

    assert context.user_data.get("pending_input") == "add tests"
    update.message.reply_text.assert_awaited_once()

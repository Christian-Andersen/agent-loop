"""Tests for agent tools."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_loop.config import AgentDeps
from agent_loop.settings import Settings
from agent_loop.tools import call_opencode


@pytest.mark.asyncio
async def test_call_opencode_returns_stdout() -> None:
    """Should return opencode's stdout."""
    settings = Settings()
    deps = AgentDeps(settings=settings)
    ctx = MagicMock()
    ctx.deps = deps

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"done", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await call_opencode(ctx, "write a test")

    assert result == "done"


@pytest.mark.asyncio
async def test_call_opencode_uses_custom_binary() -> None:
    """Should respect opencode_binary setting."""
    settings = Settings(opencode_binary="/custom/opencode")
    deps = AgentDeps(settings=settings)
    ctx = MagicMock()
    ctx.deps = deps

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"ok", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        await call_opencode(ctx, "hello")
        mock_exec.assert_called_once_with(
            "/custom/opencode",
            "hello",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )


@pytest.mark.asyncio
async def test_call_opencode_includes_stderr() -> None:
    """Should include stderr in output when present."""
    settings = Settings()
    deps = AgentDeps(settings=settings)
    ctx = MagicMock()
    ctx.deps = deps

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"out", b"err")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await call_opencode(ctx, "test")

    assert "out" in result
    assert "err" in result


@pytest.mark.asyncio
async def test_call_opencode_timeout_kills() -> None:
    """Should kill process on timeout and return partial output."""
    settings = Settings()
    deps = AgentDeps(settings=settings)
    ctx = MagicMock()
    ctx.deps = deps

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=[asyncio.TimeoutError, (b"partial", b"")])

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await call_opencode(ctx, "test")

    mock_proc.kill.assert_called_once()
    assert "partial" in result

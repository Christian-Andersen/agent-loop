"""Tests for settings module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from agent_loop.config import load_settings
from agent_loop.settings import Settings


class TestSettings:
    """Tests for Settings."""

    def test_default_values(self) -> None:
        """Optional fields should have defaults."""
        s = Settings()
        assert s.vllm_url == "http://localhost:8001/v1"
        assert s.vllm_model == "Qwen/Qwen3.5-4B"
        assert s.opencode_binary == "opencode"

    def test_frozen(self) -> None:
        """Settings should be immutable."""
        s = Settings()
        with pytest.raises(ValidationError):
            s.vllm_url = "http://other:8000/v1"  # type: ignore[misc]


class TestLoadSettings:
    """Tests for load_settings."""

    def test_loads_required(self) -> None:
        """Should return Settings instance."""
        with patch.dict("os.environ", {}, clear=True):
            s = load_settings()
            assert isinstance(s, Settings)

    def test_uses_defaults(self) -> None:
        """Should use defaults for missing env vars."""
        with patch.dict("os.environ", {}, clear=True):
            s = load_settings()
            assert s.vllm_url == "http://localhost:8001/v1"

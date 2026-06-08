"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for agent-loop.

    Automatically reads from .env and process environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    vllm_url: str = "http://localhost:8001/v1"
    vllm_model: str = "Qwen/Qwen3.5-4B"
    git_user_name: str = "Agent Loop"
    git_user_email: str = "agent@localhost"
    workspace_dir: str = "/tmp/agent-loop"  # noqa: S108
    opencode_binary: str = "opencode"

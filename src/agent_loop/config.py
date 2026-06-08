"""Environment configuration and mutable agent deps."""

from __future__ import annotations

from dataclasses import dataclass

from .settings import Settings


@dataclass
class AgentDeps:
    """Mutable per-run dependencies wrapping frozen Settings."""

    settings: Settings
    current_project: str = ""


def load_settings() -> Settings:
    """Load application settings from environment variables."""
    return Settings()

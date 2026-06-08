"""Environment configuration and mutable agent deps."""

from __future__ import annotations

from dataclasses import dataclass, field

from .settings import Settings


@dataclass
class AgentDeps:
    """Mutable per-run dependencies wrapping frozen Settings."""

    settings: Settings
    current_project: str = ""
    todo_path: str = field(default="TODO.md")

    def __post_init__(self) -> None:
        """Ensure todo_path defaults to TODO.md when empty."""
        if not self.todo_path:
            object.__setattr__(self, "todo_path", "TODO.md")


def load_settings() -> Settings:
    """Load application settings from environment variables."""
    return Settings()

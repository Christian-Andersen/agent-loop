"""PydanticAI tools for the agent loop."""

from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger
from pydantic_ai import RunContext  # noqa: TC002

from .config import AgentDeps  # noqa: TC001
from .git_ops import checkout_branch, clone_repo, commit_all, status_summary


async def call_opencode(ctx: RunContext[AgentDeps], prompt: str) -> str:
    """Invoke opencode with a coding prompt and return its output.

    opencode may ask questions back — re-invoke with answers baked
    into a richer prompt.
    """
    binary = ctx.deps.settings.opencode_binary
    proc = await asyncio.create_subprocess_exec(
        binary,
        prompt,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
    except TimeoutError:
        proc.kill()
        stdout, stderr = await proc.communicate()
        text = (stdout or b"").decode()
        err = (stderr or b"").decode()
        logger.warning("opencode timed out after 300s")
        return f"{text}\n--- stderr ---\n{err}" if err else text

    text = (stdout or b"").decode()
    err = (stderr or b"").decode()
    if err:
        text += f"\n--- stderr ---\n{err}"
    return text


async def clone_repository(ctx: RunContext[AgentDeps], url: str, repo_name: str) -> str:
    """Clone a git repository into the workspace."""
    settings = ctx.deps.settings
    workspace = Path(settings.workspace_dir) / repo_name
    path = clone_repo(url, str(workspace), settings.git_user_name, settings.git_user_email)
    ctx.deps.current_project = repo_name
    return f"Cloned {repo_name} to {path}"


async def create_branch(ctx: RunContext[AgentDeps], branch: str) -> str:
    """Create a new git branch in the current project."""
    repo = ctx.deps.current_project
    if not repo:
        return "No project selected."
    path = Path(ctx.deps.settings.workspace_dir) / repo
    return checkout_branch(str(path), branch)


async def commit_changes(ctx: RunContext[AgentDeps], message: str) -> str:
    """Stage all changes and commit in the current project."""
    repo = ctx.deps.current_project
    if not repo:
        return "No project is currently checked out."
    path = Path(ctx.deps.settings.workspace_dir) / repo
    return commit_all(str(path), message)


async def show_status(ctx: RunContext[AgentDeps]) -> str:
    """Show git status and recent log for the current project."""
    repo = ctx.deps.current_project
    if not repo:
        return "No project is currently checked out."
    path = Path(ctx.deps.settings.workspace_dir) / repo
    return status_summary(str(path))

"""Git helper functions."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def setup_git_config(path: str, name: str, email: str) -> None:
    """Configure git user name and email in the given repo."""
    _git("config", "user.name", name, cwd=path)
    _git("config", "user.email", email, cwd=path)


def clone_repo(url: str, target_path: str, name: str, email: str) -> str:
    """Clone a git repository and configure git identity.

    Returns the path to the cloned repo.
    """
    path = Path(target_path)
    if path.exists():
        return str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = _git("clone", url, str(path))
    if result.returncode != 0:
        return f"git clone failed:\n{result.stderr}"
    setup_git_config(str(path), name, email)
    return str(path)


def checkout_branch(path: str, branch: str) -> str:
    """Create a new branch and check it out."""
    result = _git("checkout", "-b", branch, cwd=path)
    if result.returncode != 0:
        return f"branch checkout failed:\n{result.stderr}"
    return f"Switched to branch {branch}"


def commit_all(path: str, message: str) -> str:
    """Stage all changes and commit with the given message."""
    add = _git("add", "-A", cwd=path)
    if add.returncode != 0:
        return f"git add failed:\n{add.stderr}"
    commit = _git("commit", "-m", message, cwd=path)
    if commit.returncode != 0:
        return commit.stdout or commit.stderr or "nothing to commit"
    return commit.stdout


def status_summary(path: str) -> str:
    """Return a human-readable git status and recent log."""
    status = _git("status", "--short", cwd=path)
    log = _git("log", "--oneline", "-10", cwd=path)
    out = "--- git status ---\n"
    out += status.stdout or "(clean)"
    out += "\n--- recent commits ---\n"
    out += log.stdout or "(no commits)"
    return out

"""CLI entry point for agent-loop."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from loguru import logger

from .agent import create_agent
from .config import AgentDeps, load_settings
from .git_ops import checkout_branch

if TYPE_CHECKING:
    from .settings import Settings


def _check_vllm(settings: Settings) -> None:
    """Fail early if the vLLM endpoint is unreachable."""
    health_url = settings.vllm_url.rstrip("/v1").rstrip("/") + "/health"
    try:
        response = httpx.get(health_url, timeout=10)
        if response.status_code != httpx.codes.OK:
            logger.error("vLLM not reachable at {} (status {})", health_url, response.status_code)
            sys.exit(1)
    except httpx.ConnectError:
        logger.error("vLLM connection refused at {}", health_url)
        sys.exit(1)
    except httpx.TimeoutException:
        logger.error("vLLM health check timed out at {}", health_url)
        sys.exit(1)


def cmd_chat(settings: Settings) -> None:
    """Start the Telegram bot (interactive mode)."""
    _check_vllm(settings)
    bot = build_bot(settings)
    logger.info("Starting Telegram bot polling...")
    bot.run_polling()


async def cmd_fix(settings: Settings, prompt: str, repo_dir: str, branch: str) -> None:
    """Run a one-shot fix in the given repo directory."""
    _check_vllm(settings)

    repo_name = Path(repo_dir).name
    deps = AgentDeps(settings=settings, current_project=repo_name)

    # Checkout branch
    branch_msg = checkout_branch(repo_dir, branch)
    logger.info("{}", branch_msg)

    agent = create_agent(settings, "fix")
    result = await agent.run(prompt, deps=deps)
    output = str(result.output)

    if "[UNANSWERED]" in output:
        logger.error("Question: {}", output)
        sys.exit(1)

    sha = subprocess.run(  # noqa: ASYNC221
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    print(f"SUCCESS\nCommit: {sha}\nBranch: {branch}\nOutput: {output[:500]}")  # noqa: T201


async def cmd_classify(settings: Settings, text: str) -> None:
    """Classify an issue description."""
    _check_vllm(settings)
    deps = AgentDeps(settings=settings)
    agent = create_agent(settings, "classify")
    result = await agent.run(text, deps=deps)
    print(result.output)  # noqa: T201


async def cmd_scan(settings: Settings, path: str) -> None:
    """Scan a repository for issues."""
    _check_vllm(settings)
    repo_name = Path(path).name
    deps = AgentDeps(settings=settings, current_project=repo_name)
    agent = create_agent(settings, "scan")
    result = await agent.run(
        f"Scan the repository at {path} for issues. Output each finding as a JSON line.",
        deps=deps,
    )
    print(result.output)  # noqa: T201


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="agent-loop: local autonomous coding agent")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("chat", help="Start Telegram bot")

    fix_parser = sub.add_parser("fix", help="Run a one-shot fix in a repo")
    fix_parser.add_argument("prompt", help="Description of the fix")
    fix_parser.add_argument("--repo-dir", required=True, help="Path to the cloned repo")
    fix_parser.add_argument("--branch", default="fix/auto", help="Branch to create")

    classify_parser = sub.add_parser("classify", help="Classify an issue")
    classify_parser.add_argument("text", help="Issue title or body")

    scan_parser = sub.add_parser("scan", help="Scan a repo for issues")
    scan_parser.add_argument("path", help="Path to the repository")

    args = parser.parse_args()
    settings = load_settings()

    if args.command == "chat":
        cmd_chat(settings)
    elif args.command == "fix":
        asyncio.run(cmd_fix(settings, args.prompt, args.repo_dir, args.branch))
    elif args.command == "classify":
        asyncio.run(cmd_classify(settings, args.text))
    elif args.command == "scan":
        asyncio.run(cmd_scan(settings, args.path))


# Import at bottom to avoid circular import at module level
from .telegram_bot import build_bot  # noqa: E402

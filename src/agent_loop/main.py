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
from .git_ops import commit_all
from .todo import mark_done, parse_tasks, read_todo, write_todo

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


def cmd_loop(settings: Settings, todo_path: str) -> None:
    """Sequentially run opencode for each incomplete task in TODO.md."""
    content = read_todo(todo_path)
    tasks = parse_tasks(content)
    total = sum(1 for t in tasks if not t.done)

    if total == 0:
        logger.info("No pending tasks in {}", todo_path)
        return

    done = 0
    for i, task in enumerate(tasks):
        if task.done:
            continue
        done += 1
        logger.info("[{done}/{total}] {text}", done=done, total=total, text=task.text)

        result = subprocess.run(  # noqa: S603
            [settings.opencode_binary, task.text],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

        if result.returncode != 0:
            logger.error("opencode exited with status {}", result.returncode)
            continue

        content = mark_done(content, i)
        write_todo(todo_path, content)
        commit_all(".", f"[agent-loop] {task.text}")
        logger.info("Task marked done and committed")

    logger.info("Processed {done}/{total} tasks", done=done, total=total)


async def cmd_orchestrate(settings: Settings, todo_path: str) -> None:
    """Use an LLM orchestrator to drive work through TODO.md tasks."""
    deps = AgentDeps(settings=settings, current_project=Path.cwd().name, todo_path=todo_path)
    content = read_todo(todo_path)
    agent = create_agent(settings, "orchestrate")
    result = await agent.run(
        f"Here is the TODO list:\n\n{content}\n\nWork through the incomplete tasks one at a time.",
        deps=deps,
    )
    print(result.output)  # noqa: T201


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="agent-loop: local autonomous coding agent")
    sub = parser.add_subparsers(dest="command", required=True)

    loop_parser = sub.add_parser("loop", help="Sequential for-loop over TODO.md tasks")
    loop_parser.add_argument("--todo", default="TODO.md", help="Path to TODO.md (default: TODO.md)")

    orch_parser = sub.add_parser("orchestrate", help="LLM-driven orchestrator over TODO.md tasks")
    orch_parser.add_argument("--todo", default="TODO.md", help="Path to TODO.md (default: TODO.md)")

    args = parser.parse_args()
    settings = load_settings()

    if args.command == "loop":
        cmd_loop(settings, args.todo)
    elif args.command == "orchestrate":
        _check_vllm(settings)
        asyncio.run(cmd_orchestrate(settings, args.todo))

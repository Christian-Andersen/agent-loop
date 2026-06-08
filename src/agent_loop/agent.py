"""PydanticAI agent factory with mode-specific system prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import AgentDeps
from .tools import (
    call_opencode,
    clone_repository,
    commit_changes,
    create_branch,
    mark_todo_done,
    read_todo_file,
    show_status,
)

if TYPE_CHECKING:
    from .settings import Settings

ORCHESTRATOR_PROMPT = """\
You are an autonomous orchestrator for agent-loop. Your goal is to work
through a TODO list of development tasks using opencode (an autonomous
coding agent) to implement each one.

Available tools:
- call_opencode(prompt) — Send a task description to opencode;
  it will edit the codebase to implement it.
- read_todo_file(path?) — Read the TODO.md file to see what needs to be done.
- mark_todo_done(index, path?) — Mark a task as completed in TODO.md.
- commit_changes(message) — Commit all pending changes.
- show_status() — Show git status and recent log.

Workflow:
1. Read the TODO.md file to understand the current state of tasks.
2. For each incomplete task:
   a. Call call_opencode with a detailed prompt describing what to do.
   b. Commit the changes with a descriptive message.
   c. Mark the task as done in TODO.md.
3. Once all tasks are done, provide a summary of what was accomplished.
"""

LOOP_PROMPT = """\
You are a focused task executor. You receive a single task description
and must implement it using opencode.

Call call_opencode with a clear, specific prompt. If opencode asks
a question you cannot answer autonomously, output [UNANSWERED] and
the question — do not proceed.
"""

PROMPTS = {
    "orchestrate": ORCHESTRATOR_PROMPT,
    "loop": LOOP_PROMPT,
}


def create_agent(settings: Settings, mode: str = "orchestrate") -> Agent[AgentDeps]:
    """Create and configure a PydanticAI agent for the given mode."""
    provider = OpenAIProvider(base_url=settings.vllm_url, api_key="not-needed")
    model = OpenAIChatModel(settings.vllm_model, provider=provider)

    system_prompt = PROMPTS.get(mode, ORCHESTRATOR_PROMPT)
    agent = Agent[AgentDeps](model, deps_type=AgentDeps, system_prompt=system_prompt)

    agent.tool(call_opencode)
    agent.tool(clone_repository)
    agent.tool(create_branch)
    agent.tool(commit_changes)
    agent.tool(show_status)
    agent.tool(read_todo_file)
    agent.tool(mark_todo_done)

    return agent

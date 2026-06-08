"""PydanticAI agent factory with mode-specific system prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import AgentDeps
from .tools import call_opencode, clone_repository, commit_changes, create_branch, show_status

if TYPE_CHECKING:
    from .settings import Settings

DEV_PROMPT = """\
You are a long-running autonomous coding agent working through Telegram.

WORKFLOW:
1. When given a project goal, clone_repository the repo, then create a step-by-step plan.
2. Work through each step:
   a. call_opencode with a clear, specific coding prompt.
   b. If opencode asks a question you can answer, re-invoke with answer baked in.
   c. If you cannot answer, prefix it with [PRODUCT QUESTION] and continue.
   d. After each step, commit_changes("step N: description").
3. Use [STEP X/Y] for progress, [ALL DONE] when complete.
"""

FIX_PROMPT = """\
You are a focused fix agent. You receive a description of a single code change.

WORKFLOW:
1. The repo is already cloned and a branch is checked out.
2. call_opencode with the fix description.
3. If opencode asks a question you cannot answer autonomously,
   output [UNANSWERED] and the question — do not proceed.
4. commit_changes with the fix description.
5. Output SUCCESS.
"""

CLASSIFY_PROMPT = """\
You are an issue classifier. Given an issue title and body, classify it.

Respond with exactly one of: BUG, FEATURE, QUESTION, OTHER
Then on a new line provide a short reason.
"""

SCAN_PROMPT = """\
You are a code scanner. Given a repository path, examine the codebase and
identify issues. For each finding output a JSON line:
{"severity":"high|medium|low","file":"path","issue":"description","line":N}

Focus on:
- Security vulnerabilities
- Unhandled errors
- Code quality issues
- Missing tests or documentation
"""

PROMPTS = {
    "dev": DEV_PROMPT,
    "fix": FIX_PROMPT,
    "classify": CLASSIFY_PROMPT,
    "scan": SCAN_PROMPT,
}


def create_agent(settings: Settings, mode: str = "dev") -> Agent[AgentDeps]:
    """Create and configure a PydanticAI agent for the given mode."""
    provider = OpenAIProvider(base_url=settings.vllm_url, api_key="not-needed")
    model = OpenAIChatModel(settings.vllm_model, provider=provider)

    system_prompt = PROMPTS.get(mode, DEV_PROMPT)
    agent = Agent[AgentDeps](model, deps_type=AgentDeps, system_prompt=system_prompt)

    agent.tool(call_opencode)
    agent.tool(clone_repository)
    agent.tool(create_branch)
    agent.tool(commit_changes)
    agent.tool(show_status)

    return agent

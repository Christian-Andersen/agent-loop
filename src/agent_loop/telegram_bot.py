"""Telegram bot handlers and autonomous session management."""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any

from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .agent import create_agent
from .config import AgentDeps

if TYPE_CHECKING:
    from telegram import Message, Update
    from telegram.ext import CallbackContext

    from .settings import Settings


def _extract_repo(text: str) -> str | None:
    m = re.search(r"(?:repo(?:sitory)?:?\s*)([\w.-]+(?:/[\w.-]+)?)", text, re.IGNORECASE)
    return m.group(1) if m else None


def _build_prompt(ud: dict[str, Any]) -> str:
    goal = ud.get("goal", "")
    repo = ud.get("repo_name", "")
    pending = ud.pop("pending_input", None)
    history = ud.get("history", [])

    parts = [f"Project: {repo}. Goal: {goal}."]
    if history:
        parts.append("\nRecent progress:")
        parts.extend(entry[:600] for entry in history[-3:])
        parts.append("\nContinue working. End with [ALL DONE] when complete.")
    else:
        parts.append("\nClone the repo, create a plan, and start working. After each step use commit_changes.")
    if pending:
        parts.append(f"\nUser message: {pending}")
    return "\n".join(parts)


async def start_command(update: Update, context: CallbackContext) -> None:  # noqa: ARG001
    """Handle /start — welcome message."""
    if update.message is None:
        return
    await update.message.reply_text(
        "I'm your autonomous coding agent. Give me a project goal and repo URL.\n"
        "Example: 'Build a CLI log parser. Repo: git@example.com/user/parser.git'\n\n"
        "/status — check progress\n/push — commit and push\n/stop — stop session"
    )


async def status_command(update: Update, context: CallbackContext) -> None:
    """Handle /status — show current progress."""
    if update.message is None:
        return
    ud: dict[str, Any] = context.user_data if context.user_data is not None else {}
    if not ud.get("active"):
        await update.message.reply_text("No active session.")
        return
    deps = AgentDeps(settings=context.application.bot_data["settings"], current_project=ud.get("repo_name", ""))
    agent = create_agent(context.application.bot_data["settings"], "dev")
    try:
        result = await agent.run("Provide a status summary.", deps=deps)
        await update.message.reply_text(str(result.output)[:2000])
    except Exception:  # noqa: BLE001
        logger.exception("Status check failed")
        await update.message.reply_text("Failed to get status.")


async def push_command(update: Update, context: CallbackContext) -> None:
    """Handle /push — commit and summarize."""
    if update.message is None:
        return
    ud: dict[str, Any] = context.user_data if context.user_data is not None else {}
    deps = AgentDeps(settings=context.application.bot_data["settings"], current_project=ud.get("repo_name", ""))
    agent = create_agent(context.application.bot_data["settings"], "dev")
    try:
        result = await agent.run("Commit all changes and summarise what was done.", deps=deps)
        await update.message.reply_text(str(result.output)[:2000])
    except Exception:  # noqa: BLE001
        logger.exception("Push failed")
        await update.message.reply_text("Failed to commit changes.")


async def stop_command(update: Update, context: CallbackContext) -> None:
    """Handle /stop — gracefully stop session."""
    if update.message is None:
        return
    ud: dict[str, Any] = context.user_data if context.user_data is not None else {}
    ud["active"] = False
    await update.message.reply_text("Session will stop after the current step completes.")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming text — start or continue a session."""
    msg = update.message
    if msg is None or msg.text is None:
        return

    ud: dict[str, Any] = context.user_data if context.user_data is not None else {}
    text = msg.text

    if ud.get("active"):
        ud["pending_input"] = text
        await msg.reply_text("Noted, I'll consider this on my next step.")
        return

    repo_url = _extract_repo(text) or ""
    ud["active"] = True
    ud["goal"] = text
    ud["repo_url"] = repo_url
    ud["history"] = []

    await msg.reply_text(f"Starting session for: {repo_url or 'unknown repo'}\nUse /status to check in.")
    asyncio.create_task(_autonomous_loop(msg, ud, context.application.bot_data["settings"]))  # noqa: RUF006


async def _autonomous_loop(msg: Message, ud: dict[str, Any], settings: Settings) -> None:
    """Background task running the agent in a loop."""
    while ud.get("active", True):
        deps = AgentDeps(settings=settings, current_project=ud.get("repo_name", ""))
        agent = create_agent(settings, "dev")
        prompt = _build_prompt(ud)

        try:
            result = await agent.run(prompt, deps=deps)
            output = str(result.output)
        except Exception:  # noqa: BLE001
            logger.exception("Agent run failed")
            await msg.reply_text("Step failed. Stopping session.")
            ud["active"] = False
            break

        ud.setdefault("history", []).append(output)
        await msg.reply_text(output[:2000])

        if "[ALL DONE]" in output.upper() or "all steps complete" in output.lower():
            ud["active"] = False
            await msg.reply_text("All steps complete! Send a new goal to start again.")
            break

        await asyncio.sleep(1)

    ud["active"] = False


def build_bot(settings: Settings) -> Application:
    """Build the Telegram bot Application with all handlers."""
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("push", push_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application

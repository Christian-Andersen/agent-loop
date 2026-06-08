"""TODO.md parsing and manipulation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TODO_ITEM_RE = re.compile(r"^- \[([ x])\] (.+)$", re.MULTILINE)


@dataclass
class TodoTask:
    """A single task parsed from a TODO.md file."""

    text: str
    done: bool
    index: int


def read_todo(path: str) -> str:
    """Read the full contents of a TODO.md file."""
    return Path(path).read_text()


def write_todo(path: str, content: str) -> None:
    """Write content back to a TODO.md file."""
    Path(path).write_text(content)


def parse_tasks(content: str) -> list[TodoTask]:
    """Parse all checklist items from TODO.md content."""
    tasks: list[TodoTask] = []
    for m in TODO_ITEM_RE.finditer(content):
        tasks.append(
            TodoTask(
                text=m.group(2),
                done=m.group(1) == "x",
                index=len(tasks),
            )
        )
    return tasks


def mark_done(content: str, index: int) -> str:
    """Mark the task at 0-based *task* index as done.

    Returns updated content string.  No-op if task is already done.
    """
    count = 0
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = TODO_ITEM_RE.match(line)
        if m:
            if count == index and m.group(1) != "x":
                lines[i] = f"- [x] {m.group(2)}\n"
                break
            count += 1
    return "".join(lines)

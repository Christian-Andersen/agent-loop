"""Tests for TODO.md parsing and manipulation."""

from __future__ import annotations

import tempfile
from pathlib import Path

from agent_loop.todo import TODO_ITEM_RE, mark_done, parse_tasks, read_todo, write_todo

SAMPLE = """\
# Tasks

- [ ] First task: do this
- [x] Second task: done
- [ ] Third task
"""


class TestParseTasks:
    """Tests for parse_tasks."""

    def test_parses_all_items(self) -> None:
        """Should find all checklist items."""
        tasks = parse_tasks(SAMPLE)
        assert len(tasks) == 3

    def test_marks_done_correctly(self) -> None:
        """Should identify done vs pending."""
        tasks = parse_tasks(SAMPLE)
        assert tasks[0].done is False
        assert tasks[1].done is True
        assert tasks[2].done is False

    def test_extracts_text(self) -> None:
        """Should extract description after checkbox."""
        tasks = parse_tasks(SAMPLE)
        assert tasks[0].text == "First task: do this"
        assert tasks[1].text == "Second task: done"
        assert tasks[2].text == "Third task"

    def test_sets_indices(self) -> None:
        """Should assign sequential indices."""
        tasks = parse_tasks(SAMPLE)
        for i, t in enumerate(tasks):
            assert t.index == i


class TestMarkDone:
    """Tests for mark_done."""

    def test_marks_pending_as_done(self) -> None:
        """Should change [ ] to [x]."""
        updated = mark_done(SAMPLE, 0)
        assert "- [x] First task" in updated
        assert "- [ ] Third task" in updated

    def test_already_done_is_noop(self) -> None:
        """Should not change already-done tasks."""
        updated = mark_done(SAMPLE, 1)
        assert "- [x] Second task" in updated
        assert updated == SAMPLE  # no change

    def test_out_of_index_noop(self) -> None:
        """Should not crash on invalid index."""
        updated = mark_done(SAMPLE, 99)
        assert updated == SAMPLE


class TestReadWrite:
    """Tests for read_todo / write_todo."""

    def test_read_write_roundtrip(self) -> None:
        """Should preserve content through write+read."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "TODO.md"
            write_todo(str(path), SAMPLE)
            content = read_todo(str(path))
            assert content == SAMPLE


class TestRegex:
    """Tests for the TODO_ITEM_RE pattern."""

    def test_matches_checkbox(self) -> None:
        """Should match both pending and done."""
        assert TODO_ITEM_RE.match("- [ ] task")
        assert TODO_ITEM_RE.match("- [x] task")

    def test_skips_non_item(self) -> None:
        """Should not match non-checklist lines."""
        assert not TODO_ITEM_RE.match("# Heading")
        assert not TODO_ITEM_RE.match("Some text")
        assert not TODO_ITEM_RE.match("- [ ]")  # no text after checkbox
        assert not TODO_ITEM_RE.match("- [a] task")  # invalid checkbox

# agent-loop

Local autonomous coding agent loop backed by an OpenAI-compatible LLM (vLLM).
Reads tasks from a `TODO.md` file and drives [opencode](https://opencode.ai) to implement them.

## Commands

- `loop` — Sequential for-loop over tasks in TODO.md, calling opencode for each
- `orchestrate` — LLM-driven orchestrator that decides the order and approach

Both accept `--todo <path>` (default: `TODO.md`).

## Requirements

- Python 3.13+
- A running OpenAI-compatible endpoint (default `http://localhost:8001/v1`)
- [opencode](https://opencode.ai) installed on `PATH`

## Setup

```sh
uv sync
```

Configure via environment variables or `.env`:

| Variable | Default |
|---|---|
| `VLLM_URL` | `http://localhost:8001/v1` |
| `VLLM_MODEL` | `Qwen/Qwen3.5-4B` |
| `GIT_USER_NAME` | `Agent Loop` |
| `GIT_USER_EMAIL` | `agent@localhost` |
| `WORKSPACE_DIR` | `/tmp/agent-loop` |
| `OPENCODE_BINARY` | `opencode` |

## Development

```sh
just ci    # sync → audit → lint/typecheck → test
just test  # uv run python -m pytest
just check # prek (ruff + ty)
```

## Modes

**`loop`** — A simple Python for-loop. Parses `TODO.md`, finds all `- [ ]` items, and runs `opencode` for each one. On success it marks the task `[x]` and commits.

**`orchestrate`** — An LLM agent reads the TODO.md, decides which task to tackle, calls opencode via tools, commits, marks done, and repeats until everything is finished.

## TODO.md format

```markdown
# Tasks

- [ ] Implement the frobnicator
- [x] Write unit tests
- [ ] Add error handling
```

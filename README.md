# Claude Code hooks demo

Three small [Claude Code hooks](https://code.claude.com/docs/en/hooks), from the Chennaipy talk
"Claude Code Hooks" (November 2026). Each hook is one short Python file with no dependencies.

| Hook | Runs | What it does |
|---|---|---|
| [`session_check.py`](hooks/session_check.py) | **SessionStart**: when Claude Code opens | Checks `uv` and `ruff` are installed and warns if you are on `main`. Never blocks |
| [`prompt_guard.py`](hooks/prompt_guard.py) | **UserPromptSubmit**: before a prompt is sent | Blocks prompts with an AWS key, password, Aadhaar, PAN, mobile number or blocked word |
| [`command_guard.py`](hooks/command_guard.py) | **PreToolUse**: before Claude runs a shell command | Denies `sudo`, `rm -rf`, reading `.env`, force-push to `main`, SQL `DROP`/`DELETE`, `pip install` |

[`.claude/settings.json`](.claude/settings.json) turns them on for this folder only.

## Try it

```bash
git clone https://github.com/arockiaraj1994/claude-hooks-demo
cd claude-hooks-demo
./setup_demo.sh          # copies the demo to ~/hooks-demo with its own git repo on main
cd ~/hooks-demo && claude
```

Then follow [DEMO.md](DEMO.md).

Without Claude, pipe JSON into a hook to see its answer:

```bash
echo '{"prompt":"My key is AKIAEXAMPLEKEY000000"}' | python3 hooks/prompt_guard.py; echo "exit $?"
echo '{"tool_input":{"command":"sudo rm -rf /tmp/x"}}' | python3 hooks/command_guard.py
echo '{}' | python3 hooks/session_check.py
```

## How a hook answers

| Answer | Meaning |
|---|---|
| `exit 0`, nothing printed | Carry on |
| `exit 2`, message on stderr | Block (here: the prompt is not sent) |
| JSON `"permissionDecision": "deny"` | Stop a tool call; Claude reads the reason and tries another way |
| JSON `systemMessage` / `additionalContext` | A message for you / a note for Claude |

## Other files

- `hooks.log`: each hook adds one line per decision (never the prompt). Watch it with `tail -f hooks.log`.
- `watch_api.py`: prints how much data the demo session sends to Claude's servers (Linux, uses `ss`).
  A blocked prompt prints nothing: it never left the laptop.
- `app.py`: a tiny app, so Claude has something to look at.
- `tests/test_hooks.py`: `uv run pytest`.

All keys, names and ID numbers in this repo are fake. These hooks are examples for a talk, not a
complete security tool: pattern checks can be worked around, so treat them as guard rails.

## Licence

MIT

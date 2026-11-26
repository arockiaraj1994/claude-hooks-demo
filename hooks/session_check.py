"""SessionStart hook: runs once, when Claude Code opens in this folder.

Two checks, and it never blocks:
    1. Are uv and ruff installed?
    2. Are we on main? The rule here is: work on a feature branch.

The JSON we print has two parts:
    systemMessage      -> shown to you
    additionalContext  -> a note for Claude
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EVENT = "SessionStart"


def log(decision: str, detail: str = "") -> None:
    """Add one line to hooks.log, so you can watch the hooks work. Never the prompt itself."""
    line = f"{time.strftime('%H:%M:%S')}  {EVENT:<16}  {decision:<5}  {detail}\n"
    with open(Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "hooks.log", "a") as f:
        f.write(line)


def main() -> int:
    # 1. Tools: only look for them on PATH, nothing is installed.
    missing = [tool for tool in ("uv", "ruff") if shutil.which(tool) is None]
    if missing:
        tools = f"⚠️  {' and '.join(missing)} not found. Run: uv tool install ruff"
    else:
        tools = "✅ uv and ruff found"

    # 2. Branch: ask git which branch this folder is on.
    git = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    branch_name = git.stdout.strip()
    if branch_name in ("main", "master"):
        branch = f"⚠️  You are on {branch_name}. Create a feature branch first: git switch -c feat/<name>"
        note = f"The session is on {branch_name}. Do not commit to it; ask for a feature branch first."
    else:
        branch = f"✅ On branch {branch_name or '(none)'}"
        note = "Work is on a feature branch."

    # 3. Log, then answer: messages for you, a note for Claude.
    log("warn" if "⚠️" in tools + branch else "ok", f"branch {branch_name or '(none)'}")
    answer = {
        "systemMessage": tools + "\n" + branch,
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note},
    }
    print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())

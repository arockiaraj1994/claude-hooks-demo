"""PreToolUse hook: runs before every shell (Bash) command Claude wants to run.

To stop a command we print JSON with "deny" and a reason. Claude reads the
reason and tries another way. If we print nothing, the command runs.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

# "reason Claude sees": pattern
RULES = {
    "sudo is not allowed here": r"\bsudo\b",
    "deleting whole folders is not allowed here": r"\brm\s+-[a-zA-Z]*(?:r[a-zA-Z]*f|f[a-zA-Z]*r)",
    "reading .env and key files is not allowed here": r"\b(?:cat|less|more|head|tail)\b[^|;&]*(?:\.env\b|\.pem\b)",
    "force-pushing to main is not allowed here": r"\bgit\s+push\b(?=.*(?:--force\b|\s-f\b))(?=.*\b(?:main|master)\b)",
    "dropping or deleting database data is not allowed here": r"(?i)\b(?:drop\s+(?:table|database)|delete\s+from|truncate)\b",
    "this project uses uv: run `uv add <package>` instead of pip install": r"\bpip3?\s+install\b",
}

EVENT = "PreToolUse"


def log(decision: str, detail: str = "") -> None:
    """Add one line to hooks.log, so you can watch the hooks work. Never the prompt itself."""
    line = f"{time.strftime('%H:%M:%S')}  {EVENT:<16}  {decision:<5}  {detail}\n"
    with open(Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "hooks.log", "a") as f:
        f.write(line)


def main() -> int:
    # 1. Read the command.
    command = json.load(sys.stdin)["tool_input"]["command"]

    # 2. Collect every rule it breaks.
    broken = [reason for reason, pattern in RULES.items() if re.search(pattern, command)]

    # 3. Nothing broken: print nothing, the command runs.
    if not broken:
        log("allow", command[:60])
        return 0

    # 4. Deny it and tell Claude why.
    log("deny", "; ".join(broken))
    reason = "Blocked by a project hook: " + "; ".join(broken) + ". Find a way without it."
    answer = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())

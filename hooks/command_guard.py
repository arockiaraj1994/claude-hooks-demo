"""PreToolUse hook: runs before every shell (Bash) command Claude wants to run.

To stop a command we print JSON with "deny" and a reason. Claude reads the
reason and tries another way. If we print nothing, the command runs.
"""

import json
import re
import sys

# "reason Claude sees": pattern
RULES = {
    "sudo is not allowed here": r"\bsudo\b",
    "deleting whole folders is not allowed here": r"\brm\s+-[a-zA-Z]*(?:r[a-zA-Z]*f|f[a-zA-Z]*r)",
    "reading .env and key files is not allowed here": r"\b(?:cat|less|more|head|tail)\b[^|;&]*(?:\.env\b|\.pem\b)",
    "force-pushing to main is not allowed here": r"\bgit\s+push\b(?=.*(?:--force\b|\s-f\b))(?=.*\b(?:main|master)\b)",
    "dropping or deleting database data is not allowed here": r"(?i)\b(?:drop\s+(?:table|database)|delete\s+from|truncate)\b",
    "this project uses uv: run `uv add <package>` instead of pip install": r"\bpip3?\s+install\b",
}


def main() -> int:
    # 1. Read the command.
    command = json.load(sys.stdin)["tool_input"]["command"]

    # 2. Collect every rule it breaks.
    broken = [reason for reason, pattern in RULES.items() if re.search(pattern, command)]

    # 3. Nothing broken: print nothing, the command runs.
    if not broken:
        return 0

    # 4. Deny it and tell Claude why.
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

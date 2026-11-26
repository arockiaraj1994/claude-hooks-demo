"""UserPromptSubmit hook: runs after you press Enter, before the prompt is sent.

We answer with an exit code:
    exit 0  -> the prompt is sent to Claude
    exit 2  -> the prompt is blocked; what we print to stderr is shown to you
"""

import json
import re
import sys

# What a prompt must not contain: "what it is": pattern. All values here are fake examples.
RULES = {
    "an AWS access key": r"AKIA[0-9A-Z]{16}",
    "a private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "a password": r"(?i)\bpassword\s*[:=]\s*\S+",
    "an Aadhaar number": r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b",
    "a PAN": r"\b[A-Z]{3}[PCHFATBLJG][A-Z]\d{4}[A-Z]\b",
    "an Indian mobile number": r"(?:\+91[ -]?)?\b[6-9]\d{4}[ -]?\d{5}\b",
    "a blocked word": r"(?i)project kaveri|project marina",
}


def main() -> int:
    # 1. Read the prompt.
    prompt = json.load(sys.stdin)["prompt"]

    # 2. Check it against every rule. Show only 4 characters, so the warning does not leak it.
    problems = []
    for name, pattern in RULES.items():
        match = re.search(pattern, prompt)
        if match:
            problems.append(f"{name} ({match.group()[:4]}****)")

    # 3. Nothing found: send it.
    if not problems:
        return 0

    # 4. Found something: block it, and do not repeat the prompt on screen.
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "suppressOriginalPrompt": True}}))
    print("Blocked: this prompt looks like it contains", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    print("Remove it and send the prompt again.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

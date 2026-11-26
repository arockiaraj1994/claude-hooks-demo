"""Run each hook the way Claude Code does: JSON on stdin, then read the answer."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS = Path(__file__).parent.parent / "hooks"


def run(hook: str, event: dict, cwd: Path | None = None) -> subprocess.CompletedProcess:
    log_dir = cwd or Path(tempfile.mkdtemp())
    return subprocess.run(
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=cwd,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(log_dir)},
    )


# UserPromptSubmit
@pytest.mark.parametrize(
    "prompt, reason",
    [
        ("My key is AKIAEXAMPLEKEY000000", "an AWS access key (AKIA****)"),
        ("Aadhaar 2345 6789 0123", "an Aadhaar number (2345****)"),
        ("PAN ABCPE1234K", "a PAN (ABCP****)"),
        ("Call me on 98765 43210", "an Indian mobile number"),
        ("password = hunter2", "a password"),
        ("Status of Project Kaveri?", "a blocked word"),
    ],
)
def test_prompt_blocked(prompt, reason):
    result = run("prompt_guard.py", {"prompt": prompt})
    assert result.returncode == 2
    assert reason in result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["suppressOriginalPrompt"] is True


def test_prompt_allowed():
    result = run("prompt_guard.py", {"prompt": "What files are in this folder?"})
    assert result.returncode == 0
    assert result.stdout == "" and result.stderr == ""


# PreToolUse
@pytest.mark.parametrize(
    "command, reason",
    [
        ("sudo rm -rf /var/log/myapp", "sudo is not allowed"),
        ("rm -rf build", "deleting whole folders"),
        ("cat .env", "reading .env"),
        ("git push --force origin main", "force-pushing to main"),
        ("psql -c 'DROP TABLE users'", "dropping or deleting"),
        ("python3 db.py \"DELETE FROM fees WHERE year = 2024\"", "dropping or deleting"),
        ("psql -c 'TRUNCATE fees'", "dropping or deleting"),
        ("pip install requests", "uv add"),
    ],
)
def test_command_denied(command, reason):
    result = run("command_guard.py", {"tool_input": {"command": command}})
    answer = json.loads(result.stdout)["hookSpecificOutput"]
    assert answer["permissionDecision"] == "deny"
    assert reason in answer["permissionDecisionReason"]


@pytest.mark.parametrize("command", ["python3 db.py \"SELECT * FROM fees\"", "ls -la", "uv add requests", "git push origin feat/demo", "rm old.log"])
def test_command_allowed(command):
    result = run("command_guard.py", {"tool_input": {"command": command}})
    assert result.returncode == 0 and result.stdout == ""


# SessionStart
def git_repo(path: Path, branch: str) -> Path:
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=path, check=True)
    return path


def test_session_warns_on_main(tmp_path):
    answer = json.loads(run("session_check.py", {}, cwd=git_repo(tmp_path, "main")).stdout)
    assert "You are on main" in answer["systemMessage"]
    assert "Do not commit" in answer["hookSpecificOutput"]["additionalContext"]


def test_session_ok_on_feature_branch(tmp_path):
    answer = json.loads(run("session_check.py", {}, cwd=git_repo(tmp_path, "feat/demo")).stdout)
    assert "✅ On branch feat/demo" in answer["systemMessage"]


def test_log_line_never_has_the_prompt(tmp_path):
    run("prompt_guard.py", {"prompt": "My key is AKIAEXAMPLEKEY000000"}, cwd=tmp_path)
    line = (tmp_path / "hooks.log").read_text()
    assert "UserPromptSubmit" in line and "block" in line and "an AWS access key" in line
    assert "AKIAEXAMPLE" not in line

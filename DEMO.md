# Demo script

About 10 minutes. The **Demo** slide is the cue to switch to the terminal.
All keys, names and ID numbers below are fake.

> Always start `claude` inside the demo folder (`~/hooks-demo`). The hooks are set up in its
> `.claude/settings.json`, so they only run for a session started there.

## Before the talk

| # | Check | How |
|---|---|---|
| 1 | Reset the demo folder | `./setup_demo.sh`. It wipes and recreates `~/hooks-demo` on `main` |
| 2 | The hooks answer | Run the backup commands at the end of this file |
| 3 | `uv` and `ruff` installed | `uv --version && ruff --version`. If ruff is missing: `uv tool install ruff` |
| 4 | Only the demo hooks are on | In a rehearsal, run `/hooks`. If a plugin adds its own hooks, turn it off in `~/hooks-demo/.claude/settings.local.json` (`setup_demo.sh` keeps that file) |
| 4b | Plain Claude on stage | Your own CLAUDE.md, memory and MCP servers can show up in answers. In `~/hooks-demo/.claude/settings.local.json` set `"autoMemoryEnabled": false` and `"claudeMdExcludes": ["<home>/.claude/CLAUDE.md"]`, then start Claude with `claude --strict-mcp-config` |
| 5 | No trust prompt on stage | Rehearse once in `~/hooks-demo` and accept the folder trust prompt. `./setup_demo.sh` keeps the same path, so the trust stays |
| 6 | Screen | Terminal font 18 or larger. Three panes: Claude on the left, hook log top right, network watch bottom right |

## Step 0: set the scene (30 seconds)

Top-right pane:
```bash
tail -f ~/hooks-demo/hooks.log
```
> "This pane shows every time a hook runs. It logs the decision only, never the prompt."

Bottom-right pane:
```bash
python3 ~/hooks-demo/watch_api.py
```
It waits until Claude starts, then prints a line such as `sent 18.2 KB  received 3.1 KB` only when
the session sends or receives data.

> "This pane shows how much data this session sends to Claude's servers. It is encrypted, so we see
> whether something is sent, not what."

Optional: open `.claude/settings.json` and point at the three event names.

## Step 1: SessionStart

Left pane:
```bash
cd ~/hooks-demo
claude
```
**You should see:**
```
✅ uv and ruff found
⚠️  You are on main. Create a feature branch first: git switch -c feat/<name>
```
> "Before I typed anything, a script checked two things. My tools are there, but I am on main.
> It warns me and tells Claude not to commit to main. It does not block."

Fix it: `/exit`, then
```bash
git switch -c feat/demo
claude
```
**You should see:** `✅ uv and ruff found` and `✅ On branch feat/demo`.

## Step 2: UserPromptSubmit, a secret

Type:
```
My test key is AKIAEXAMPLEKEY000000, can you check it?
```
**You should see:** `Blocked: this prompt looks like it contains - an AWS access key (AKIA****)`.
The prompt is not shown again, the hook log shows `block  an AWS access key`, and the network pane prints nothing.

> "Nothing moved on the network pane. The key never left my laptop."

## Step 3: UserPromptSubmit, personal data

A blocked prompt stays in the input box. Clear it first (`Ctrl+U`).


Type:
```
Send the fee reminder to Priya, PAN ABCPE1234K, Aadhaar 2345 6789 0123
```
**You should see:** blocked, with `an Aadhaar number (2345****)` and `a PAN (ABCP****)`.

> "These are plain regular expressions at the top of prompt_guard.py. Anyone can add one."

Then a normal prompt:
```
What files are in this folder?
```
**You should see:** Claude answers, the hook log shows `allow`, and the network pane prints the kilobytes sent and received.

## Step 4: PreToolUse, sudo

Type:
```
Clean up the old log files in /var/log/myapp using sudo
```
**You should see:** Claude tries a `sudo ...` command, and it is denied with
`Blocked by a project hook: sudo is not allowed here`, and the hook log shows `PreToolUse  deny`. Claude reads the reason and suggests another way.

> "This check is on what Claude does, not what I type. Claude got the reason and changed its plan."

`/var/log/myapp` does not exist, so nothing is deleted. Approve harmless commands such as `ls`;
decline anything else. If Claude does not try sudo, type: `Run this exactly: sudo rm -rf /var/log/myapp/old`

## Step 4b: PreToolUse, deleting database rows

`demo.db` is a small SQLite database with a `fees` table (5 fake rows). Optional: show it first with
`python3 db.py "SELECT * FROM fees"` in the bottom-right pane before starting the watch.

Type:
```
Delete the 2024 rows from the fees table in demo.db
```
**You should see:** Claude looks at the table, then tries a `DELETE FROM fees ...` and it is denied with
`dropping or deleting database data is not allowed here`. The hook log shows `PreToolUse  deny`.
Claude does not try to get around it: it tells you to run it yourself or change the rule.

> "Same hook, different rule. DELETE, TRUNCATE and DROP never reach the database from Claude.
> If someone really needs it, a person runs it."

## Step 5 (optional, needs Wi-Fi): pip vs uv

Type:
```
Run pip install requests
```
**You should see:** `pip install requests` is denied with `this project uses uv`, and Claude runs
`uv add requests` instead.

> "A deny reason does not only stop things. It steers Claude to the way this project works."

## Step 6: what is on

Type `/hooks`.
> "This lists every hook that is on, and where it was set up."

`/exit` and switch back to the deck.

## If something goes wrong

| Problem | What to do |
|---|---|
| No branch warning at start | You are already on a branch. `git switch main`, start `claude` again, or run `./setup_demo.sh` |
| A prompt is not blocked | Show the hook with the backup commands below |
| Network pane prints a line on a blocked prompt | Claude Code sometimes talks to the server in the background. Send the allowed prompt so people can compare |
| Hooks do not run | Hooks are read when the session starts. Exit and run `claude` again in `~/hooks-demo` |

Do not type commands with a leading `!` in Claude: they run straight in your shell and skip the hooks.

## Backup: run the hooks without Claude (works offline)

```bash
cd ~/hooks-demo
echo '{"prompt":"My key is AKIAEXAMPLEKEY000000"}' | python3 hooks/prompt_guard.py; echo "exit $?"
echo '{"tool_input":{"command":"sudo rm -rf /tmp/x"}}' | python3 hooks/command_guard.py
echo '{}' | python3 hooks/session_check.py
```
You should see `exit 2` with the block message, a JSON `deny`, and the two session lines.

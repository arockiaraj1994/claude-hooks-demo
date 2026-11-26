#!/usr/bin/env bash
# Copy the demo to its own folder with a fresh git repo on main.
# Run it again to reset the demo. It wipes the target first.
#
# Usage: ./setup_demo.sh [target]      (default: ~/hooks-demo)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-$HOME/hooks-demo}"

if [ -e "$TARGET" ] && [ ! -f "$TARGET/.hooks-demo" ]; then
  echo "Refusing to wipe $TARGET: it is not a hooks demo folder." >&2
  exit 1
fi

# Keep your own .claude/settings.local.json (for example, plugins turned off) across resets.
LOCAL="$TARGET/.claude/settings.local.json"
SAVED=""
if [ -f "$LOCAL" ]; then SAVED="$(cat "$LOCAL")"; fi

rm -rf "$TARGET"
mkdir -p "$TARGET"
cp -r "$HERE/.claude" "$HERE/hooks" "$HERE/app.py" "$HERE/db.py" "$HERE/pyproject.toml" "$HERE/watch_api.py" "$TARGET/"
if [ -n "$SAVED" ]; then printf '%s\n' "$SAVED" > "$LOCAL"; fi
touch "$TARGET/.hooks-demo" "$TARGET/hooks.log"
printf '.hooks-demo\nhooks.log\ndemo.db\n.claude/settings.local.json\n' > "$TARGET/.gitignore"

cd "$TARGET"
git init -q -b main
git add -A
git -c user.name="Hooks Demo" -c user.email="demo@localhost" commit -q -m "Hooks demo"

python3 db.py "SELECT count(*) FROM fees" > /dev/null   # creates demo.db

echo "Demo ready in $TARGET (branch: main)"
echo "Next: cd $TARGET && claude"

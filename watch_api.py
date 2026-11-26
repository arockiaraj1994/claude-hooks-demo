"""Show how much data the demo Claude session sends to Claude's servers. No sudo needed.

Every second it reads the byte counters Linux keeps for each network
connection (`ss -tinp`), for the `claude` process started in this folder,
to api.anthropic.com only. It prints a line only when data moves:

    Blocked prompt -> no new line (nothing left the laptop)
    Allowed prompt -> a line like "sent 18.2 KB   received 3.1 KB"

The traffic is encrypted, so this shows WHETHER something was sent, not WHAT.

Usage: python3 watch_api.py
"""

import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

API_HOST = "api.anthropic.com"
DEMO_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent).resolve()


def api_addresses() -> set[str]:
    """The IP addresses api.anthropic.com points to right now."""
    return {str(info[4][0]) for info in socket.getaddrinfo(API_HOST, 443)}


def demo_claude_pids() -> set[str]:
    """Process IDs of `claude` sessions started in the demo folder."""
    pids = set()
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            name = (proc / "comm").read_text().strip()
            folder = Path(os.readlink(proc / "cwd"))
        except OSError:
            continue  # The process ended, or it belongs to another user.
        if name == "claude" and folder == DEMO_DIR:
            pids.add(proc.name)
    return pids


def read_counters(ips: set[str], pids: set[str]) -> dict[str, tuple[int, int]]:
    """Bytes sent and received so far, for each connection from our pids to the API.

    `ss -tinp` prints two lines per connection: the addresses and process,
    then an indented line with counters like bytes_sent:1234 bytes_received:5678.
    """
    output = subprocess.run(["ss", "-tinpH"], capture_output=True, text=True).stdout
    counters = {}
    connection = None  # The connection we are reading, if it is one we watch.

    for line in output.splitlines():
        if not line.startswith((" ", "\t")):
            # First line: State Recv-Q Send-Q Local Peer Process
            fields = line.split()
            local, peer = fields[3], fields[4]
            peer_ip = peer.rsplit(":", 1)[0].strip("[]")
            ours = any(f"pid={pid}," in line for pid in pids)
            connection = local if (peer_ip in ips and ours) else None
        elif connection:
            # Second line: the counters for that connection.
            values = dict(
                part.split(":", 1) for part in line.split() if part.startswith("bytes_")
            )
            sent = int(values.get("bytes_sent", 0))
            received = int(values.get("bytes_received", 0))
            counters[connection] = (sent, received)
    return counters


def kb(count: int) -> str:
    return f"{count / 1024:6.1f} KB"


def main() -> int:
    ips = api_addresses()
    print(f"Watching {API_HOST} ({', '.join(sorted(ips))})")
    print(f"for the claude session started in {DEMO_DIR}")
    print("A line appears only when data moves. Press Ctrl+C to stop.\n")

    # Start from the current counters, so we only show traffic from now on.
    last = read_counters(ips, demo_claude_pids())
    waiting_shown = False

    try:
        while True:
            pids = demo_claude_pids()
            if not pids and not waiting_shown:
                print("Waiting for claude to start in the demo folder...")
                waiting_shown = True

            now = read_counters(ips, pids)
            sent = sum(s - last.get(conn, (0, 0))[0] for conn, (s, _) in now.items())
            received = sum(
                r - last.get(conn, (0, 0))[1] for conn, (_, r) in now.items()
            )
            last = now

            if sent > 0 or received > 0:
                stamp = datetime.now().strftime("%H:%M:%S")
                print(f"{stamp}  sent {kb(sent)}   received {kb(received)}", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

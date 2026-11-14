#!/usr/bin/env python3
"""Say which of the tools Lem uses this machine has.

Onboarding runs it first, so a repository is never set up for a flow its machine cannot run. It
prints one row per tool as JSON and exits 1 when a required one is absent. An optional tool that
is absent is not an error: its row says what the skill does without it, and onboarding tells the
owner that.

    doctor.py
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Where each agent keeps a user's skills; the agterm skill is looked for in all of them.
SKILL_HOMES = (".claude/skills", ".agents/skills", ".codex/skills", ".config/opencode/skills")


def version(command: list[str]) -> str | None:
    try:
        ran = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = (ran.stdout or ran.stderr).strip().splitlines()
    return lines[0] if ran.returncode == 0 and lines else None


def tool(name: str, need: str, used_for: str, without_it: str, binary: str, probe: list[str] | None = None) -> dict:
    path = shutil.which(binary)
    return {
        "name": name, "need": need, "found": path is not None,
        "detail": (version([path, *probe]) if path and probe else None) or path,
        "used_for": used_for, "without_it": without_it,
    }


def agterm() -> list[dict]:
    row = tool(
        "agterm", "required", "the reviewer's pane, pages for the owner, and a session per task",
        "no reviewer pane and no mailbox: the pair flow cannot run", "agtermctl", ["--version"],
    )
    row["in_session"] = bool(os.environ.get("AGTERM_SESSION_ID"))
    homes = [str(Path.home() / home / "agterm") for home in SKILL_HOMES
             if (Path.home() / home / "agterm" / "SKILL.md").is_file()]
    skill = {
        "name": "agterm skill", "need": "required", "found": bool(homes), "detail": ", ".join(homes) or None,
        "used_for": "how an agent drives agterm: overlays, sessions, panes",
        "without_it": "an agent has agterm and does not know its commands; install it from agterm's Help menu",
    }
    return [row, skill] if row["found"] else [row]


def cronn() -> dict:
    row = tool(
        "cronn", "optional", "a scheduled retro, a scheduled pass over the review queue, and the agents' free hours",
        "retro and review run only when someone types them; onboarding offers to install it", "cronn",
    )
    env_file = Path(os.environ.get("CRONN_CONFIG_DIR") or Path.home() / ".config" / "cronn") / "cronn.env"
    port = None
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("CRONN_PORT="):
                port = line.split("=", 1)[1].strip().strip("\"'")
    row["running"] = False
    if port:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/v1/status", timeout=2) as answer:
                row["running"] = answer.status == 200
        except (urllib.error.URLError, OSError, ValueError):
            pass
    return row


def main() -> None:
    tools = [
        tool("git", "required", "worktrees, branches and the task state directory", "nothing runs", "git", ["--version"]),
        tool("revmux", "required", "the review rounds over a landed range, with the project's lenses",
             "no review of a landed change; the skill refuses to queue what it cannot review", "revmux", ["--version"]),
        *agterm(),
        tool("huddle", "optional", "a question to the owner as a page with the options side by side",
             "the question is asked in the terminal; link skills/huddle/bin/huddle into a directory on PATH", "huddle"),
        tool("plannotator", "optional", "the owner marks up a plan or a diff, and the notes come back to the agent",
             "the webrev skill shows documents, and a diff is read in the terminal; recommended, so say how to install it",
             "plannotator", ["--version"]),
        tool("jev", "optional", "sorting backlog items by who can act on them next",
             "the backlog is listed without verdicts", "jev"),
        tool("codex", "optional", "a reviewer of another model family, and half of each persona panel",
             "the reviewer is a second Claude; agreement between model families is not measured", "codex", ["--version"]),
        tool("claude", "optional", "a Claude Code reviewer, or the coordinator", "the reviewer must be Codex", "claude", ["--version"]),
        tool("mailbox-chat", "required", "messages between the coordinator and the reviewer in the other pane",
             "the two agents cannot talk; install agterm's two-agent mailbox chat recipe from its cookbook", "mailbox-chat.py"),
        cronn(),
    ]
    ok = all(row["found"] for row in tools if row["need"] == "required")
    print(json.dumps({"ok": ok, "tools": tools}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

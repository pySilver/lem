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
# Where Claude Code keeps a user's agent definitions. The setup links Lem's builder there.
BUILDER = Path(".claude") / "agents" / "lem-builder.md"


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


def claude() -> list[dict]:
    row = tool("claude", "optional", "a Claude Code reviewer, or the coordinator", "the reviewer must be Codex", "claude", ["--version"])
    # The user's definition, or the one of the repository this runs in: Claude Code takes the
    # project's before the user's, and a trial links Lem into one repository only.
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
        inside = top.stdout.strip() if top.returncode == 0 else ""
    except OSError:
        # no git on this machine: its own row says so, and this one looks in the home only
        inside = ""
    places = [Path(inside) / BUILDER] if inside else []
    file = next((place for place in [*places, Path.home() / BUILDER] if place.is_file()), Path.home() / BUILDER)
    builder = {
        "name": "lem-builder agent", "need": "required", "found": file.is_file(), "detail": str(file) if file.is_file() else None,
        "used_for": "the builder Lem starts for each task of a plan in Claude Code",
        "without_it": f"Claude Code has no agent of that name and Lem starts no builder; link agents/lem-builder.md of Lem's clone to ~/{BUILDER}",
    }
    # Only a machine with Claude Code needs Claude Code's form of the builder.
    return [row, builder] if row["found"] else [row]


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
             "the question is asked in the terminal; link skills/lem-huddle/bin/huddle into a directory on PATH", "huddle"),
        tool("plannotator", "optional", "the owner marks up a plan or a diff, and the notes come back to the agent",
             "the lem-webrev skill shows documents, and a diff is read in the terminal; recommended, so say how to install it",
             "plannotator", ["--version"]),
        tool("jev", "optional", "the queue of the owner's corrections that the retro reads, and backlog items sorted by who can act next",
             "corrections are learned in the session only and the backlog is listed without verdicts; recommended, so offer it",
             "jev"),
        tool("codex", "optional", "a reviewer of another model family, and half of each persona panel",
             "the reviewer is a second Claude; agreement between model families is not measured", "codex", ["--version"]),
        *claude(),
        tool("mailbox-chat", "required", "messages between the coordinator and the reviewer in the other pane",
             "the two agents cannot talk; install agterm's two-agent mailbox chat recipe from its cookbook", "mailbox-chat.py"),
        cronn(),
    ]
    ok = all(row["found"] for row in tools if row["need"] == "required")
    print(json.dumps({"ok": ok, "tools": tools}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

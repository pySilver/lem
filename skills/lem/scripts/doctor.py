#!/usr/bin/env python3
"""Say which of the tools Lem uses this machine has.

Onboarding runs it first, so a repository is never set up for a flow its machine cannot run. It
prints one row per tool as JSON and exits 1 when a required one is absent. An optional tool that
is absent is not an error: its row says what the skill does without it, and onboarding tells the
owner that. A recommended tool is one Lem does not bring and a developer is better off with: its
row has the guide to install it by, and Lem installs it only on the developer's yes.

    doctor.py

It loads under an old `python3` too, so that a machine whose first `python3` is the one its system
ships gets a row that says so, not a traceback.
"""

from __future__ import annotations

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
# Where Claude Code keeps what it installed as plugins: its own list, and the folders themselves.
PLUGINS = Path(".claude") / "plugins"


def python() -> dict:
    return {
        "name": "python3", "need": "required", "found": sys.version_info >= (3, 11), "detail": f"{sys.version.split()[0]} at {sys.executable}",
        "used_for": "every script of Lem; the settings file is read with a module that came with Python 3.11",
        "without_it": "no script of Lem runs; put a python3 of 3.11 or newer first on PATH",
    }


# The guides of the tools Lem recommends and never copies in: recipes of the agterm cookbook.
COOKBOOK = "https://github.com/umputun/agterm/tree/master/cookbook/"


def checkouts() -> set[str]:
    """This checkout's root and its main checkout's, by their real paths; empty outside a repository or with no git."""
    found = set()
    for args in (["--show-toplevel"], ["--path-format=absolute", "--git-common-dir"]):
        try:
            ran = subprocess.run(["git", "rev-parse", *args], capture_output=True, text=True, check=False)
        except OSError:
            return set()
        if ran.returncode == 0 and ran.stdout.strip():
            path = Path(ran.stdout.strip())
            # the common directory is `.git` of the main checkout
            found.add(os.path.realpath(path.parent if args[-1] == "--git-common-dir" and path.name == ".git" else path))
    return found


def plugin_named(name: str) -> str | None:
    """`the plugin NAME@MARKETPLACE` when Claude Code's list of installed plugins has one of that
    name that this repository gets: one installed for the user, or for this repository. Else None."""
    # That file is the agent's own and may read any way: whatever is not the shape known here is no answer.
    try:
        listed = json.loads((Path.home() / PLUGINS / "installed_plugins.json").read_text())
    except (OSError, ValueError):
        return None
    plugins = listed.get("plugins") if isinstance(listed, dict) else None
    if not isinstance(plugins, dict):
        return None
    here = checkouts()
    for key, installs in plugins.items():
        if not isinstance(key, str) or key.split("@")[0] != name:
            continue
        # An install for the user counts everywhere, one for a project only in that project. An
        # entry that says neither is a shape this check does not know, and is no answer.
        for entry in installs if isinstance(installs, list) else []:
            if not isinstance(entry, dict):
                continue
            where = entry.get("projectPath")
            if entry.get("scope") in ("user", "managed") or (isinstance(where, str) and os.path.realpath(where) in here):
                return f"the plugin {key}"
    return None


def skill(name: str, used_for: str, without_it: str, need: str = "required", guide: str | None = None) -> dict:
    """A skill an agent loads by name: in a skills folder of the home or of this repository, or installed as a plugin of Claude Code."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
        inside = [Path(top.stdout.strip())] if top.returncode == 0 and top.stdout.strip() else []
    except OSError:
        inside = []
    places = [base / home / name for base in [*inside, Path.home()] for home in SKILL_HOMES]
    found = next((str(place) for place in places if (place / "SKILL.md").is_file()), None)
    if found is None:
        # Claude Code's own list of installed plugins; where that file is absent or reads another
        # way, the plugin's folder with the skill in it counts too.
        found = plugin_named(name)
    if found is None:
        cache = Path.home() / PLUGINS / "cache"
        found = next((str(file.parent) for file in sorted(cache.glob(f"*/{name}/*/**/skills/{name}/SKILL.md"))), None) if cache.is_dir() else None
    row = {"name": f"{name} skill", "need": need, "found": found is not None, "detail": found, "used_for": used_for, "without_it": without_it}
    return {**row, "guide": guide} if guide else row


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
    row = tool("claude", "required", "the agent that runs `/lem`, and a reviewer of the same family",
               "nothing runs `/lem`: Claude Code is the one agent Lem has a harness file for", "claude", ["--version"])
    # The user's definition, or the one of the repository this runs in: Claude Code takes the
    # project's before the user's, and a trial links Lem into one repository only.
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
        inside = top.stdout.strip() if top.returncode == 0 else ""
    except OSError:
        # no git on this machine: its own row says so, and this one looks in the home only
        inside = ""
    places = [Path(inside) / BUILDER] if inside else []
    file = next((place for place in [*places, Path.home() / BUILDER] if place.is_file()), None)
    # Lem installed as a plugin brings the agent under the plugin's name, with no file in an agents folder.
    plugin = plugin_named("lem")
    builder = {
        "name": "lem-builder agent", "need": "required", "found": bool(file or plugin),
        "detail": str(file) if file else f"lem:lem-builder, from {plugin}" if plugin else None,
        "used_for": "the builder Lem starts for each task of a plan in Claude Code",
        "without_it": f"Claude Code has no agent of that name and Lem starts no builder; link agents/lem-builder.md of Lem's clone to ~/{BUILDER} "
                      "with Lem's setup, or install Lem as a plugin. A plugin loaded for one session by a flag is not seen by this check",
    }
    # Only a machine with Claude Code needs Claude Code's form of the builder.
    return [row, builder] if row["found"] else [row]


def codex() -> list[dict]:
    row = tool("codex", "optional", "a reviewer of another model family, and half of each persona panel",
               "the reviewer is a second Claude; agreement between model families is not measured", "codex", ["--version"])
    file = Path.home() / ".codex" / "agents" / "persona.toml"
    persona = {
        "name": "codex persona agent", "need": "optional", "found": file.is_file(), "detail": str(file) if file.is_file() else None,
        "used_for": "the second half of a persona panel: each persona answered by the other model family",
        "without_it": f"a panel has the answers of one model family, so a split between two is not seen; the lem-panel skill says what {file} holds",
    }
    # only a machine with Codex can run that half
    return [row, persona] if row["found"] else [row]


def project() -> list[dict]:
    """In a repository that has Lem's settings: whether it has the people a panel asks. No row anywhere else.

    The row's need is `project`, not `required`: it is about this repository and not about the
    machine, so it never fails the machine check, and the onboarding that would write the
    personas is not stopped by their absence.
    """
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    except OSError:
        return []
    root = Path(top.stdout.strip()) if top.returncode == 0 and top.stdout.strip() else None
    if root is None or not (root / ".lem" / "project.toml").is_file():
        return []
    row = {
        "name": "project personas", "need": "project", "found": False, "detail": None,
        "used_for": "the people a panel asks before a hard question reaches the owner: every project of Lem has two or more",
        "without_it": "the project's setup is not finished and no panel can run; `/lem init` in this repository asks who a decision "
                      "here affects and writes them, and leaves the settings that are there as they are",
    }
    # The panel's own script answers: it reads the checkout and, for a worktree older than the
    # cast, the default branch, so this row and a panel never disagree about one repository.
    cast = Path(__file__).resolve().parents[2] / "lem-panel" / "scripts" / "cast.py"
    asked = subprocess.run([sys.executable, "-B", str(cast), "--repo", str(root)], capture_output=True, text=True, check=False)
    if asked.returncode != 0:
        return [{**row, "detail": (asked.stderr or asked.stdout).strip().removeprefix("cast: ")[:300] or "the panel's cast check printed nothing"}]
    try:
        found = json.loads(asked.stdout)
        count = len(found["personas"])
        where = f"{found['layer']}, {found['source']}"
    except (ValueError, KeyError, TypeError):
        return [{**row, "detail": "the panel's cast check printed no JSON"}]
    detail = f"{count} ({where})" + (": a panel needs a second person who would notice other things" if count == 1 else "")
    return [{**row, "found": count > 0, "detail": detail}]


def cronn() -> dict:
    row = tool(
        "cronn", "optional", "a scheduled retro, a night plan, and the agents' free hours",
        "a retro and a night plan run only when someone types them; onboarding offers to install it", "cronn",
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
        python(),
        tool("git", "required", "worktrees, branches and the task state directory", "nothing runs", "git", ["--version"]),
        tool("revmux", "required", "the review rounds over a landed range, with the project's lenses",
             "no review of a landed change; the skill refuses to queue what it cannot review", "revmux", ["--version"]),
        skill("revmux", "how an agent runs a review round: it writes the round's context and reads the findings back",
              "an agent has the review tool and no instructions for it; install the skill that comes with revmux (its README says how)"),
        *agterm(),
        # The recommended tools: none is copied into Lem, each has a guide the developer follows,
        # and Lem installs one only on the developer's yes.
        skill("webrev", "the owner marks up a plan, a draft or any document as a rendered page, and the notes come back to the agent; "
              "the default of tools.annotate", "the owner reads the file as it is and gives the notes in the conversation",
              need="recommended", guide=COOKBOOK + "annotate-document"),
        skill("agdoc", "a page about the issue, the plan or the change in hand, for the owner's own reading",
              "no stage needs it; the owner reads the same in the conversation", need="recommended", guide=COOKBOOK + "html-doc-overlay"),
        {**tool("plannotator-tui", "recommended", "the owner marks up what a pane printed, or an agent's newest reply, from two agterm chords",
                "no stage needs it", "plannotator-tui", ["--version"]), "guide": COOKBOOK + "annotate-in-plannotator-tui"},
        tool("plannotator", "optional", "another way to mark up a plan or a draft, for an owner who names it in tools.annotate",
             "nothing is lost: webrev is the default of tools.annotate", "plannotator", ["--version"]),
        tool("jev", "optional", "backlog items sorted by who can act next, and the framing check of a question's card",
             "the backlog is listed without verdicts and a card gets no framing check; Lem's setup links its own copy for a home. "
             "The correction queue does not need this row: its hook runs Lem's copy by its path", "jev"),
        {
            "name": "OpenRouter key", "need": "optional", "found": bool(os.environ.get("OPENROUTER_API_KEY")), "detail": None,
            "used_for": "the Jev decision model, which the correction queue, the backlog's sorting and a card's framing check ask",
            "without_it": "none of the three gets an answer, and the correction hook logs each message as a failure; "
                          "put OPENROUTER_API_KEY into the environment the agent starts with",
        },
        *codex(),
        *claude(),
        tool("mailbox-chat", "required", "messages between the coordinator and the reviewer in the other pane",
             "the two agents cannot talk; install agterm's two-agent mailbox chat recipe from its cookbook, which puts mailbox-chat.py on PATH", "mailbox-chat.py"),
        skill("mailbox-chat", "how an agent sends to the other pane and reads what comes back",
              "an agent has the command and no instructions for it; the same recipe of agterm's cookbook installs the skill"),
        cronn(),
        *project(),
    ]
    ok = all(row["found"] for row in tools if row["need"] == "required")
    print(json.dumps({"ok": ok, "tools": tools}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

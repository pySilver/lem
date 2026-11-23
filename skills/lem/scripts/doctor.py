#!/usr/bin/env python3
"""Say which of the tools Lem uses this machine has.

Onboarding runs it first, so a repository is never set up for a flow its machine cannot run. It
prints one row per tool as JSON and exits 1 when a required one is absent. An optional tool that
is absent is not an error: its row says what the skill does without it, and onboarding tells the
owner that. The key of the Jev model (`JEV_API_KEY`) is optional, and required in a repository whose correction queue is
on, where without it the queue stays empty and nothing says so. A recipe of the agterm cookbook that Lem needs (webrev, the backlog) is
required, and its row has the guide to install it by. A recommended tool is one Lem does not bring
and a developer is better off with (agdoc, plannotator-tui, Plannotator, Codex): its row has the guide too, and Lem
installs it only on the developer's yes. The optional row `load gate` says under which load average the checks of a
landing start on this machine, 40 (Lem's default) with no number set, or that the gate is away, with
the line that sets one. The optional
row `handoff tokens` says past how many tokens a task's session compacts itself, `handoff tokens:
600000 (default)` with no number set, and the line that sets one. On a machine with agterm, the optional row `task picker` gives the keymap line
that starts `lem picker` with a chord, which the owner adds to agterm's keymap; a line that names the
script `picker.py` of the clone, as this check printed before, counts as there and works. The optional
row `board server` says whether the board server runs, with its addresses and its code against the
code installed here, and the line that starts it from a terminal with no agent: `lem` by the path of
Lem's marketplace clone, since the plugin puts `lem` on the PATH of Claude Code's Bash tool only, and
the clone's `bin/lem` runs the newest installed release; it never starts one. The optional row `board
notifications` says how many devices get the board's notifications and how the last push went; it
sends none. The optional row `installed Lem: NAME` comes for each repository of the server's list whose
installed Lem (Claude Code's `installed_plugins.json`) is other code than the board server runs, with
the line that updates the install there and the line that replaces the server. Four rows
are about the repository it runs in and never fail the check: its personas, the correction hook
when more than one place registers it there, the permission mode a builder in the background
meets there, and Lem's plugin when it is installed for the user and so loads in every repository.

    lem doctor

The row `python3` names the Python that Lem's commands and hooks run under, which `lem_python.py`
finds when the first `python3` is older than 3.11, and fails with the fix when there is none.
"""

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"doctor.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

# Where each agent keeps a user's skills; the agterm skill is looked for in all of them.
SKILL_HOMES = (".claude/skills", ".agents/skills", ".codex/skills", ".config/opencode/skills")
# Where a project keeps its own agent definitions: a `lem-builder` there takes the place of the plugin's.
BUILDER = Path(".claude") / "agents" / "lem-builder.md"
# Where Claude Code keeps what it installed as plugins: its own list, and the folders themselves.
PLUGINS = Path(".claude") / "plugins"


def python() -> dict:
    """The Python of 3.11 or newer that `lem` and the plugin's hooks start Lem's scripts with, found
    as they find it: the first `python3` on PATH, else the newest `python3.N`, else Homebrew's, else one uv has."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lem_python  # noqa: E402  (beside this file)

    def said(path: str) -> str:
        return ".".join(map(str, lem_python.version(path) or ("an unknown version",)))

    first = shutil.which("python3")
    found = lem_python.find()
    python3 = f"python3 is {said(first)} at {first}" if first else "python3 is not on PATH"
    if found is not None and found == first:
        detail = f"{said(found)} at {found}"
    elif found is not None:
        detail = f"{python3}; Lem's commands and hooks start {found} ({said(found)}) in its place"
    else:
        detail = f"{python3}, and no python3.N of 3.11 or newer is on PATH, nor at {' or '.join(lem_python.FALLBACKS)}, and uv has none"
    return {
        "name": "python3", "need": "required", "found": found is not None, "detail": detail,
        "used_for": "every script of Lem, its commands and its two hooks; the settings file is read with a module that came with Python 3.11",
        "without_it": f"no command of Lem runs, and the plugin's two hooks do nothing in a session; run {lem_python.FIX}",
    }


# The guides of the recipes of the agterm cookbook that Lem needs or recommends, and never copies in.
COOKBOOK = "https://github.com/umputun/agterm/tree/master/cookbook/"


def checkout_roots() -> list[Path]:
    """This checkout's root, then its main checkout's when this is a task's worktree, by their real
    paths; empty outside a repository or with no git. A file of the project's own that git does not
    track is in the main checkout only, so a worktree has no copy of it."""
    found: list[Path] = []
    for args in (["--show-toplevel"], ["--path-format=absolute", "--git-common-dir"]):
        try:
            ran = subprocess.run(["git", "rev-parse", *args], capture_output=True, text=True, check=False)
        except OSError:
            return []
        if ran.returncode == 0 and ran.stdout.strip():
            path = Path(ran.stdout.strip())
            # the common directory is `.git` of the main checkout
            real = Path(os.path.realpath(path.parent if args[-1] == "--git-common-dir" and path.name == ".git" else path))
            if real not in found:
                found.append(real)
    return found


def checkouts() -> set[str]:
    """This checkout's root and its main checkout's, by their real paths; empty outside a repository or with no git."""
    return {str(root) for root in checkout_roots()}


def plugin_installs(name: str, home: Path) -> list[tuple[str, str | None]]:
    """Each install of the plugin NAME that Claude Code's list in `home` has, as (NAME@MARKETPLACE,
    the real path of its project, or None for an install for the user)."""
    # That file is the agent's own and may read any way: whatever is not the shape known here is no answer.
    try:
        listed = json.loads((home / PLUGINS / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    plugins = listed.get("plugins") if isinstance(listed, dict) else None
    if not isinstance(plugins, dict):
        return []
    found: list[tuple[str, str | None]] = []
    for key, installs in plugins.items():
        if not isinstance(key, str) or key.split("@")[0] != name:
            continue
        # An install for the user counts everywhere, one for a project only in that project. An
        # entry that says neither is a shape this check does not know, and is no answer.
        for entry in installs if isinstance(installs, list) else []:
            if not isinstance(entry, dict):
                continue
            where = entry.get("projectPath")
            if entry.get("scope") in ("user", "managed"):
                found.append((key, None))
            elif isinstance(where, str):
                found.append((key, os.path.realpath(where)))
    return found


def plugin_named(name: str) -> str | None:
    """`the plugin NAME@MARKETPLACE` when Claude Code's list of installed plugins has one of that
    name that this repository gets: one installed for the user, or for this repository. Else None."""
    here = checkouts()
    for key, where in plugin_installs(name, Path.home()):
        if where is None or where in here:
            return f"the plugin {key}"
    return None


def plugin_skill(name: str) -> str | None:
    """`the skill PLUGIN:NAME` when an installed plugin this repository gets carries a skill NAME
    under its own name, as `tracking:backlog` carries `backlog`. Else None."""
    try:
        listed = json.loads((Path.home() / PLUGINS / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    plugins = listed.get("plugins") if isinstance(listed, dict) else None
    here = checkouts()
    for key, installs in plugins.items() if isinstance(plugins, dict) else []:
        for entry in installs if isinstance(installs, list) else []:
            if not isinstance(entry, dict) or not isinstance(entry.get("installPath"), str):
                continue
            where = entry.get("projectPath")
            gets = entry.get("scope") in ("user", "managed") or (isinstance(where, str) and os.path.realpath(where) in here)
            if gets and (Path(entry["installPath"]) / "skills" / name / "SKILL.md").is_file():
                return f"the skill {str(key).split('@')[0]}:{name}"
    return None


def settings(file: Path) -> dict:
    """A settings file of Claude Code; empty when it is absent or reads another way."""
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def enabled(key: str, home: Path, root: Path | None) -> bool:
    """Whether Claude Code turns the plugin `key` on in the repository `root` (None: outside one).
    The repository's local settings say it first, then its shared ones, then the user's
    (code.claude.com/docs/en/settings-reference, `enabledPlugins`, read 2026-11-17). With no word
    the plugin follows its manifest's `defaultEnabled`; Lem's sets none, and an install writes the word."""
    files = [root / ".claude" / "settings.local.json", root / ".claude" / "settings.json"] if root else []
    for file in [*files, home / ".claude" / "settings.json"]:
        words = settings(file).get("enabledPlugins")
        if isinstance(words, dict) and isinstance(words.get(key), bool):
            return words[key]
    return True


def lem_plugin(home: Path, root: Path | None) -> str | None:
    """`the plugin lem@MARKETPLACE` when Lem is installed as a plugin for the user or for the
    repository `root`, and the settings leave it on there. Else None."""
    real = os.path.realpath(root) if root else None
    for key, where in plugin_installs("lem", home):
        if (where is None or where == real) and enabled(key, home, root):
            return f"the plugin {key}"
    return None


# The correction hook in a settings file, in any form (`python3 /PATH/corrections.py hook`), added by hand.
HOOK_FORM = re.compile(r"corrections\.py['\"]?\s+hook\b")


def hook_entries(file: Path) -> list[dict]:
    """Each entry of the correction hook among the `UserPromptSubmit` hooks of a settings file."""
    hooks = settings(file).get("hooks")
    groups = hooks.get("UserPromptSubmit") if isinstance(hooks, dict) else None
    entries = [hook for group in groups if isinstance(group, dict) and isinstance(group.get("hooks"), list)
               for hook in group["hooks"]] if isinstance(groups, list) else []
    return [hook for hook in entries if isinstance(hook, dict) and isinstance(hook.get("command"), str) and HOOK_FORM.search(hook["command"])]


def removal(hook: dict, file: Path, shared: bool) -> str:
    """How one entry of the hook comes out of `file`: by hand, since no command of Lem's writes a
    settings file. The guide names the entry as the file holds it, so that the owner deletes that
    object from the file's `UserPromptSubmit` hooks and nothing else; an entry in the repository's
    shared settings is a change to commit too."""
    entry = json.dumps(hook, ensure_ascii=False)
    return f"delete the entry {entry} from the UserPromptSubmit hooks of {file} by hand" + (", and commit that" if shared else "")


def hook_places(home: Path, root: Path | None) -> list[dict]:
    """Each place that registers the correction hook for the repository `root` (None: outside one),
    as its name and how it comes out: the home's settings, the repository's local and shared ones,
    and Lem's plugin, which needs no removal."""
    files = [(home / ".claude" / "settings.json", False)]
    if root is not None:
        files += [(root / ".claude" / "settings.local.json", False), (root / ".claude" / "settings.json", True)]
    places = [{"where": str(file), "remove": removal(hook, file, shared)} for file, shared in files for hook in hook_entries(file)]
    plugin = lem_plugin(home, root)
    return places + ([{"where": plugin, "remove": None}] if plugin else [])


def correction_hook() -> list[dict]:
    """A row when the correction hook is registered in more than one place for this repository; no row otherwise.

    The hook comes with Lem's plugin. A second place is a settings file that names the hook too,
    and no command of Lem's takes it out: the guide names each entry to delete by hand. Its need is
    `project`, as the personas' row: it is about what this repository gets, and it never fails the
    machine check. The hook judges each message once however often it starts, so the row is about
    telling the truth, not about a wrong queue.
    """
    roots = checkout_roots()
    places = hook_places(Path.home(), roots[0] if roots else None)
    if len(places) < 2:
        return []
    extra = [place for place in places if place["remove"] is not None]
    if len(extra) < len(places):
        fix = "The plugin brings the hook, so remove each other place: " + "; ".join(f"{place['where']}: {place['remove']}" for place in extra)
    else:
        # no plugin among them: the plugin is what brings the hook
        fix = "The hook comes with Lem's plugin: install it, and remove each of these: " + "; ".join(f"{place['where']}: {place['remove']}" for place in extra)
    return [{
        "name": "correction hook", "need": "project", "found": False,
        "detail": f"registered {len(places)} times for this repository: " + ", ".join(place["where"] for place in places),
        "used_for": "the correction queue: one call of the Jev model and at most one entry for each message of the owner",
        "without_it": "Claude Code starts the hook once for each place. The first copy claims the message, so it is still judged "
                      f"once, and each other copy starts for nothing. {fix}. The check reads the settings files of the home and of "
                      "this repository and Claude Code's list of plugins; it does not see managed settings, a session's --settings, "
                      "or a plugin loaded for one session by a flag",
    }]


def skill(name: str, used_for: str, without_it: str, need: str = "required", guide: str | None = None) -> dict:
    """A skill an agent loads by name: in a skills folder of the home or of this repository, installed as a plugin of
    Claude Code, or carried by an installed plugin of another name."""
    places = [base / home / name for base in [*checkout_roots(), Path.home()] for home in SKILL_HOMES]
    found = next((str(place) for place in places if (place / "SKILL.md").is_file()), None)
    if found is None:
        # Claude Code's own list of installed plugins; where that file is absent or reads another
        # way, the plugin's folder with the skill in it counts too.
        found = plugin_named(name) or plugin_skill(name)
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


def gh() -> dict:
    """The GitHub CLI: found or not, and signed in or not. The row is optional: a machine may hold
    repositories that do not use Lem, and `lem land propose` and the board's look at GitHub say so where it is missing."""
    row = tool(
        "gh", "optional", "the pull request of each task and the board's look at the open ones, where the remote is GitHub",
        "with a GitHub remote `lem land propose` and the board's look at GitHub stop and say so; install the GitHub CLI and run `gh auth login`", "gh", ["--version"],
    )
    row["signed_in"] = False
    if row["found"]:
        try:
            row["signed_in"] = subprocess.run([shutil.which("gh") or "gh", "auth", "status"], capture_output=True, text=True, check=False, timeout=10).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            pass
        if not row["signed_in"]:
            row["detail"] = f"{row['detail']}; not signed in: `gh auth login` signs it in"
    return row


def agterm() -> list[dict]:
    row = tool(
        "agterm", "required", "a session for each task, the reviewer's pane, pages for the owner, and the companion of a plan talk",
        "`/lem` stops at once: Lem runs inside agterm only", "agtermctl", ["--version"],
    )
    row["in_session"] = bool(os.environ.get("AGTERM_SESSION_ID"))
    homes = [str(Path.home() / home / "agterm") for home in SKILL_HOMES
             if (Path.home() / home / "agterm" / "SKILL.md").is_file()]
    skill = {
        "name": "agterm skill", "need": "required", "found": bool(homes), "detail": ", ".join(homes) or None,
        "used_for": "how an agent drives agterm: overlays, sessions, panes",
        "without_it": "an agent has agterm and does not know its commands; install it from agterm's Help menu",
    }
    return [row, skill, picker()] if row["found"] else [row]


# The task picker: an agterm keymap line that starts it with a chord. The keymap is agterm's file, so
# Lem only reads it, at the place agterm reads it by default.
KEYMAP = Path(".config") / "agterm" / "keymap.conf"
# The line runs Lem's command, `bin/lem picker`. The lines this check printed before named the script
# itself, which still works: in the marketplace clone it hands over to the clone's `bin/lem picker`.
COMMAND = Path("bin") / "lem"
PICKER = Path("skills") / "lem" / "scripts" / "picker.py"
CHORD = "ctrl+cmd+t"


def marketplace_lem(home: Path, holds: Path) -> Path | None:
    """The clone of Lem's marketplace when it holds the file `holds` (a path inside Lem), or None.
    Its path outlives every update, and the plugin's own folder, named by its version, changes with
    each one, so it is never this. The clone holds the head of `main`, which no release holds, so a
    line names only its `bin/lem`, which runs the newest installed release in its place."""
    try:
        known = json.loads((home / PLUGINS / "known_marketplaces.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        known = {}
    for key, _ in plugin_installs("lem", home):
        entry = known.get(key.partition("@")[2]) if isinstance(known, dict) else None
        place = entry.get("installLocation") if isinstance(entry, dict) else None
        if isinstance(place, str) and (Path(place) / holds).is_file():
            return Path(place)
    return None


def stable_lem(home: Path) -> tuple[Path, str] | None:
    """A folder of Lem whose path outlives an update of the plugin, with what keeps it new, or None.
    First the clone of Lem's marketplace (`marketplace_lem`). Else this checkout, when it is a clone
    of Lem's repository, as for a contributor who loads it with `claude --plugin-dir`."""
    clone = marketplace_lem(home, COMMAND)
    if clone is not None:
        return clone, "Lem's marketplace clone, which never moves, and whose bin/lem runs the newest installed release"
    own = Path(__file__).resolve().parents[3]
    return (own, "this clone of Lem, which stays where it is") if (own / ".git").exists() and (own / COMMAND).is_file() else None


def keymap_runs(said: str, home: Path, scripts: tuple[Path, ...]) -> Path | None:
    """The one of SCRIPTS that the keymap line SAID runs, or None: a `command` line whose words name
    it by its absolute path or by the same path from `~/`. `bin/lem` counts only before `picker`."""
    if not said.lstrip().startswith("command"):
        return None
    try:
        words = shlex.split(said)
    except ValueError:
        words = said.split()
    for at, word in enumerate(words):
        path = home / word[2:] if word.startswith("~/") else Path(word)
        for script in scripts:
            if path == script and (script.name != "lem" or words[at + 1:at + 2] == ["picker"]):
                return script
    return None


def interpreter() -> str:
    """The python3 the keymap line names: a keymap command gets the system's PATH, whose python3 is
    older than 3.11 on a Mac. The one first on this PATH when it is the one running (its link, which
    an upgrade keeps), else the one running."""
    found = shutil.which("python3")
    return found if found and os.path.realpath(found) == os.path.realpath(sys.executable) else sys.executable


def picker() -> dict:
    """The keymap line of the task picker for this machine, and whether agterm's keymap holds it. An
    optional row: nothing of Lem needs the chord, and `/lem status SLUG` opens the same board."""
    home = Path.home()
    keymap = home / KEYMAP
    row = {"name": "task picker", "need": "optional", "found": False, "detail": None, "line": None,
           "used_for": "a chord in agterm that lists this repository's tasks, what waits for the owner first, and opens the board of the one picked"}
    found = stable_lem(home)
    if found is None:
        return {**row, "without_it": "no chord lists the tasks, and `/lem status SLUG` opens a board. No folder of Lem here keeps its path "
                                     "after an update: Lem's marketplace clone is not there, so a keymap line would name a folder the next update removes"}
    root, kept = found
    command, script = root / COMMAND, root / PICKER
    line = f'command "Lem tasks ›" {CHORD} --error-hud {shlex.quote(interpreter())} {shlex.quote(str(command))} picker'
    try:
        runs = [keymap_runs(said, home, (command, script)) for said in keymap.read_text(encoding="utf-8", errors="replace").splitlines()]
    except OSError:
        runs = []
    held = command in runs or script in runs
    detail = (f"{keymap} holds the line" if command in runs else
              f"{keymap} holds a line that runs {script}, an older form that still works; the line in its current form, to put in its "
              "place when the owner likes, is this row's line" if held else f"{keymap} has no line that runs {command} picker")
    return {**row, "found": held, "line": line, "detail": detail,
            "without_it": f"no chord lists the tasks, and `/lem status SLUG` opens a board. The owner adds the line to {keymap} and runs "
                          f"`agtermctl keymap reload`; {CHORD} is the chord unless he picks another. The line names {root}, {kept}, "
                          "and a python3 of 3.11 or newer, which a keymap command does not find on its own PATH"}


def claude() -> list[dict]:
    row = tool("claude", "required", "the agent that runs `/lem`, and a reviewer of the same family",
               "nothing runs `/lem`: Claude Code is the one agent Lem has a harness file for", "claude", ["--version"])
    # Lem's plugin brings the agent under the plugin's name, `lem:lem-builder`. A project may keep
    # its own `lem-builder` in its `.claude/agents/`, which Claude Code takes first: this checkout's,
    # or the main checkout's when git does not track it.
    file = next((place for place in (root / BUILDER for root in checkout_roots()) if place.is_file()), None)
    plugin = plugin_named("lem")
    # A plugin loaded for one session by a flag (`claude --plugin-dir DIR`) is in no list of
    # installs; the session tells its commands the plugin's folder in CLAUDE_PLUGIN_ROOT.
    session = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    loaded = Path(session) if session and (Path(session) / "agents" / "lem-builder.md").is_file() else None
    builder = {
        "name": "lem-builder agent", "need": "required", "found": bool(file or plugin or loaded),
        "detail": str(file) if file else f"lem:lem-builder, from {plugin}" if plugin
        else f"lem:lem-builder, from the plugin loaded for this session ({loaded})" if loaded else None,
        "used_for": "the builder Lem starts for each task of a plan in Claude Code",
        "without_it": "Claude Code has no agent of that name and Lem starts no builder; install Lem's plugin in this repository: "
                      "`claude plugin marketplace add pySilver/lem --scope project`, then `claude plugin install lem@lem --scope project`. "
                      "A session that loaded the plugin by a flag (`claude --plugin-dir DIR`) has the builder as lem:lem-builder all the same: "
                      "this check finds such a plugin only through CLAUDE_PLUGIN_ROOT, and this command did not get it",
    }
    # Only a machine with Claude Code needs Claude Code's form of the builder.
    return [row, builder] if row["found"] else [row]


def codex() -> list[dict]:
    # recommended: the owner's ruling "cronn is required, and Codex is highly recommended" (2026-11-18), so
    # onboarding offers it with its guide; it fails no check ("Without Codex one expert answers alone")
    row = tool("codex", "recommended", "a reviewer of another model family, the second expert of the ladder, and half of each persona panel",
               "highly recommended, since without it Claude reviews the work of Claude: "
               "the reviewer is a second Claude; an expert whose seat names codex (by default the second of seats.experts, the newest "
               "Astra of OpenAI) does not answer, so the one expert that can answer, the newest Fable of Anthropic by default, answers "
               "alone and its pick settles a decision the experts take, and the pull request is not green for such a decision; a persona "
               "panel has the answers of one model family, so a split between two is not seen", "codex", ["--version"])
    row["guide"] = "https://github.com/openai/codex"
    file = Path.home() / ".codex" / "agents" / "persona.toml"
    persona = {
        "name": "codex persona agent", "need": "optional", "found": file.is_file(), "detail": str(file) if file.is_file() else None,
        "used_for": "the second half of a persona panel: each persona answered by the other model family",
        "without_it": f"a panel has the answers of one model family, so a split between two is not seen; the lem-panel skill says what {file} holds",
    }
    # only a machine with Codex can run that half
    return [row, persona] if row["found"] else [row]


# The modes in which Claude Code asks nobody before a command: `bypassPermissions` asks nothing, and
# `auto` has a model classifier decide. Neither takes effect from a repository's own settings, only
# from the user's (code.claude.com/docs/en/settings-reference, `permissions.defaultMode`, read
# through ctx7 on 2026-11-17).
SILENT_MODES = ("bypassPermissions", "auto")
# What a builder in the background meets in each mode, for the row's `without_it`.
MODE_SAYS = {
    "default": "each command the allow list does not hold asks for permission, and the question comes up in the task's session, so the task waits; at night nobody answers",
    "acceptEdits": "an edit goes through, and each other command the allow list does not hold asks for permission in the task's session, so the task waits; at night nobody answers",
    "plan": "a builder can read and cannot edit or commit, so no task builds",
    "dontAsk": "each command the allow list does not hold is refused with no question, so a builder stops at the first one",
}


# The one line of the row when the mode is not auto: what to change, in the user's own settings,
# since a repository's settings cannot set auto (see SILENT_MODES).
TO_AUTO = ('Lem assumes auto mode: put "defaultMode": "auto" under "permissions" in your own ~/.claude/settings.json, '
           "and start a new session")


def permission_mode() -> list[dict]:
    """In a repository: the permission mode a new session starts in there, and what a builder in the
    background meets in it. No row outside a repository. The repository's local settings say it
    first, then its shared ones, then the user's; `auto` and `bypassPermissions` count only from the
    user's. Lem assumes that Claude Code runs in auto mode (the owner, 2026-11-18: "we assume that
    automode is used in codex and claude code"), so the row says that, and what to change when the
    mode is another. Its need is `project`, as the personas' row: it never fails the machine check."""
    roots = checkout_roots()
    if not roots:
        return []
    root, home = roots[0], Path.home() / ".claude" / "settings.json"
    mode, source = "default", None
    for file in (root / ".claude" / "settings.local.json", root / ".claude" / "settings.json", home):
        permissions = settings(file).get("permissions")
        said = permissions.get("defaultMode") if isinstance(permissions, dict) else None
        if not isinstance(said, str) or (said in SILENT_MODES and file != home):
            continue
        mode, source = said, file
        break
    silent = mode in SILENT_MODES
    meets = MODE_SAYS.get(mode, "a mode this check does not know; a builder may ask for permission in the task's session")
    return [{
        "name": "permission mode", "need": "project", "found": silent,
        "detail": f"{mode}, from {source}" if source else "default: no settings file names one",
        "used_for": "Lem assumes that Claude Code runs in auto mode: the builders and the leads run in the background, and a permission "
                    "prompt stops the task until someone answers in the task's session",
        "without_it": (
            "a builder asks nobody" + ("; the classifier may still refuse a step, which the owner then runs himself" if mode == "auto" else "")
            if silent else
            f"{meets}. {TO_AUTO}. "
            "Until then, the allow rules that /lem init offers for .claude/settings.local.json hold Lem's commands, git's and the checks'"
        ),
    }]


def user_plugin() -> list[dict]:
    """A row when Lem's plugin is installed for the user, and so loads in every repository of the
    machine; no row otherwise. Its need is `project`: it never fails the machine check."""
    users = [key for key, where in plugin_installs("lem", Path.home()) if where is None]
    if not users:
        return []
    return [{
        "name": "lem plugin scope", "need": "project", "found": False,
        "detail": f"{users[0]} is installed for the user, so every repository on this machine loads it",
        "used_for": "Lem's skills, its builder and its correction hook, which belong to the repositories that use Lem",
        "without_it": (
            "the skills and the hook load in every repository; the hook in a repository with no .lem/settings.toml writes nothing and costs "
            "about a tenth of a second a message (a median of 99.4 ms over 20 runs, Python 3.15.2, one Mac, 2026-11-17). "
            f"`claude plugin uninstall {users[0]} --scope user` removes that install; then `claude plugin install {users[0]} --scope project` "
            "in each repository that uses Lem"
        ),
    }]


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
    if root is None or not (root / ".lem" / "settings.toml").is_file():
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


def collects_here() -> bool:
    """Whether the correction queue is on in the repository the check runs in: this machine's
    `machine.toml` says `collect = true` under `[corrections]`, and the repository uses Lem. The
    hook's own answer, so the row and the hook never disagree."""
    # no bytecode beside the scripts, also when this file runs without -B
    sys.dont_write_bytecode = True
    import corrections

    return corrections.collects(os.getcwd())


def machine_name() -> str:
    """The machine's own settings file, as a person writes it (`~/.config/lem/machine.toml`)."""
    # beside this file, as `collects_here` finds corrections.py
    import lem_state

    return lem_state.shown(lem_state.machine_file())


# What the row of the Jev key says of where the key and the address come from (jev.py reads them)
JEV_WHERE = ("JEV_API_KEY in the environment the agent starts with, the key of the Jev model's provider; the provider is "
             "OpenRouter unless JEV_API_URL names another (then JEV_MODEL names its model)")


def jev_key() -> dict:
    """The key of the Jev decision model: JEV_API_KEY, the one name jev.py reads for it. Required
    where the correction queue is on: without it the hook writes a failure for each message to a
    file nobody reads, and the queue stays empty."""
    given = bool(os.environ.get("JEV_API_KEY"))
    url = os.environ.get("JEV_API_URL", "").strip()
    detail = f"JEV_API_KEY, to {url or 'OpenRouter'}" if given else "JEV_API_KEY is not set, and it is the one name Lem reads for the key"
    row = {"name": "Jev key", "need": "optional", "found": given, "detail": detail,
           "used_for": "the Jev decision model, which the correction queue and a card's framing check ask"}
    if collects_here():
        return {**row, "need": "required", "detail": f"{detail}; the correction queue is on here (collect = true under [corrections] in {machine_name()})",
                "without_it": "the correction hook writes each message of the owner to .lem/state/corrections.log as a failure, the queue stays "
                              f"empty, and the retro reads nothing. Put {JEV_WHERE}, or turn the "
                              "queue off for every repository on this machine with `lem corrections collect no`"}
    return {**row, "without_it": "a card's framing check gets no answer, and the correction queue, which is off here, would stay empty if it "
                                 f"were on; put {JEV_WHERE}"}


def load_gate() -> dict:
    """The load average under which the checks of a landing start on this machine. An optional row:
    with no number Lem's own (LOAD_START) holds, and the developer sets his (a laptop he keeps cool, a
    desktop he loads hard), or takes the gate away."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lem_state  # noqa: E402  (beside this file)

    row = {"name": "load gate", "need": "optional", "found": False, "line": "lem project load --start N",
           "used_for": "the checks of a landing start only while the machine's load average is below the number set for this machine"}
    load = round(os.getloadavg()[0], 1)
    cores = os.cpu_count()
    try:
        start = lem_state.load_start()
    except lem_state.StateError as error:
        return {**row, "detail": str(error), "without_it": "the checks of a landing stop at once with this error, until the file reads"}
    if start is None:
        return {**row, "detail": f"no gate on this machine (`lem project load --start none`); the load average is {load:g} now, on {cores} cores",
                "without_it": f"the checks of every landing start at once, whatever the load. `lem project load --start N` sets a number in "
                              f"{lem_state.machine_file()}, for every repository on this machine"}
    whose = "" if "start" in lem_state.machine_table("load") else ", Lem's default"
    return {**row, "found": True, "detail": f"the checks start below a load average of {start:g}{whose}; it is {load:g} now, on {cores} cores ({lem_state.machine_file()})",
            "without_it": None}


def handoff_tokens() -> dict:
    """Past how many tokens a task's session compacts itself, for every repository on this machine.
    An optional row: with no number Lem's own holds, and the row says so."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lem_state  # noqa: E402  (beside this file)

    row = {"name": "handoff tokens", "need": "optional", "line": "lem project handoff --tokens N",
           "used_for": "each task's session compacts itself past this number of tokens, with the handoff's form as its summary"}
    try:
        number = lem_state.handoff_tokens()
        written = "tokens" in lem_state.machine_table("handoff")
    except lem_state.StateError as error:
        return {**row, "found": False, "detail": str(error), "without_it": "`lem session open` stops with this error, until the file reads"}
    if number is None:
        detail = "handoff tokens: 0, so Lem sets nothing and Claude Code compacts at its own trigger"
    else:
        detail = f"handoff tokens: {number} ({'set in ' + str(lem_state.machine_file()) if written else 'default'})"
    return {**row, "found": True, "detail": detail, "without_it": None}


def board_server() -> list[dict]:
    """The board server of this machine (`lem serve`): whether one runs on the main port, its address
    on this machine and on the tailnet, and its code against the code installed here. It only asks the
    server and never starts one. An optional row: the board opens in agterm without it."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import serve  # noqa: E402  (beside this file)

    # `lem` is on the PATH of Claude Code's Bash tool only; in a terminal with no agent (a remote login)
    # the owner runs it by the path of Lem's marketplace clone, which no update moves, and whose bin/lem
    # runs the newest installed release, never the clone's own head of main
    clone = marketplace_lem(Path.home(), COMMAND)
    line = f"{shlex.quote(str(clone / 'bin' / 'lem'))} serve --ensure" if clone else "lem serve --ensure"
    row = {"name": "board server", "need": "optional", "found": False, "line": line,
           "used_for": "the boards of every repository on this machine in a browser of another device, the owner's phone through his tailnet "
                       "(`/lem serve tailscale`, one time); the first Claude Code session in a repository that uses Lem starts it"}
    without = ("the board opens in agterm only, until a Claude Code session starts in a repository that uses Lem, or `/lem serve` "
               f"runs; after a remote login with no agent, `{line}` in the terminal")
    try:
        settings = serve.serve_settings()
        found = serve.ask(settings["port"])
    except (serve.ServeError, serve.lem_state.StateError) as error:
        return [{**row, "detail": str(error), "without_it": without}]
    mine = serve.code_version()
    door = f", and the door on tailnet port {settings['tailscale_port']}" if settings["tailscale"] else ""
    if found is None:
        return [{**row, "detail": f"no server runs on port {settings['port']}{door}; the code here is {mine}", "without_it": without}]
    where = found["url"] + (f" and {found['tailscale']}" if found.get("tailscale") else "")
    code = (f"it runs {found['version']}, and the code here is {mine}: the next `lem serve --ensure` replaces it" if serve.outdated(found) else
            f"it runs {found['version']}, the code here" if found["version"] == mine else f"it runs {found['version']}, newer than the code here, {mine}")
    return [{**row, "found": True, "detail": f"pid {found['pid']} serves {where}; {code}; its log is {serve.lem_state.config() / serve.SERVE_LOG}",
             "without_it": None}]


def lem_installs(home: Path) -> list[dict]:
    """Each install of Lem in Claude Code's list in `home`: its key (`lem@MARKETPLACE`), its scope, the real
    path of its project (None for the user), its version and its folder, as the list names them."""
    try:
        listed = json.loads((home / PLUGINS / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    plugins = listed.get("plugins") if isinstance(listed, dict) else None
    found = []
    for key, installs in plugins.items() if isinstance(plugins, dict) else []:
        if not isinstance(key, str) or key.split("@")[0] != "lem":
            continue
        for entry in installs if isinstance(installs, list) else []:
            if isinstance(entry, dict) and entry.get("scope") in ("user", "managed", "project", "local"):
                where = entry.get("projectPath")
                found.append({"key": key, "scope": entry["scope"], "project": os.path.realpath(where) if isinstance(where, str) else None,
                              "version": entry.get("version") if isinstance(entry.get("version"), str) else None,
                              "folder": entry.get("installPath") if isinstance(entry.get("installPath"), str) else None})
    return found


def version_numbers(identity: str) -> tuple[int, ...] | None:
    """`version 0.1.1` as (0, 1, 1); None for a commit or a time, which have no order."""
    found = re.fullmatch(r"version (\d+(?:\.\d+)*)", identity or "")
    return tuple(int(part) for part in found[1].split(".")) if found else None


def install_rows(server: str, repositories: list[str], installs: list[dict], identity) -> list[dict]:
    """A row for each repository of the server's list whose installed Lem is other code than the board
    server runs (SERVER, `code_version`'s form): a session there runs one Lem and the server's duties
    another. IDENTITY gives an install's code by its folder and version. The install a repository gets is
    the one for its project, else the one for the user; a repository with none gets no row here."""
    rows = []
    for repository in repositories:
        real = os.path.realpath(repository)
        mine = next((entry for entry in installs if entry["project"] == real), None) or next((entry for entry in installs if entry["project"] is None), None)
        if mine is None:
            continue
        theirs = identity(mine)
        if theirs == server:
            continue
        update = f"cd {shlex.quote(repository)} && claude plugin update {mine['key']} --scope {'user' if mine['scope'] == 'managed' else mine['scope']}"
        older = version_numbers(theirs), version_numbers(server)
        which = ("the install is the older" if older[0] < older[1] else "the server is the older") if None not in older else "which is the newer is not known"
        rows.append({"name": f"installed Lem: {Path(repository).name}", "need": "optional", "found": False, "line": update, "lines": [update, "lem serve --ensure"],
                     "detail": f"{repository} has {theirs} of {mine['key']} installed for the {mine['scope']}, and the board server runs {server}; {which}",
                     "used_for": "one Lem for a repository's task sessions and for the board server's duties over them",
                     "without_it": "a task's session runs other code than the server that wakes it and merges for it: run the first line in a terminal "
                                   "and restart that repository's sessions, or `lem serve --ensure` from the newer Lem to replace the server"})
    return rows


def installed_lem() -> list[dict]:
    """The rows of `install_rows` for this machine: the server's code from `GET /api/server`, the
    repositories of its list (`lem_state.workspaces`), and Claude Code's list of installed plugins.
    Nothing when no server runs or a file does not read: the row `board server` says that."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import serve  # noqa: E402  (beside this file)

    try:
        found = serve.ask(serve.serve_settings()["port"])
        repositories = serve.lem_state.workspaces()
    except (serve.ServeError, serve.lem_state.StateError):
        return []
    if not found or not found.get("version"):
        return []

    def identity(entry: dict) -> str:
        folder = Path(entry["folder"]) if entry.get("folder") else None
        if folder is not None and (folder / ".claude-plugin" / "plugin.json").is_file():
            return serve.code_version(folder)
        return f"version {entry['version']}" if entry.get("version") else "an unknown version"

    return install_rows(found["version"], repositories, lem_installs(Path.home()), identity)


def board_notifications() -> list[dict]:
    """The board's notifications on the owner's devices (lem_push): how many devices turned them on, and
    when the last push went with each push service's answer. It reads Lem's home folder and sends
    nothing. An optional row: the board shows what waits without them."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lem_push  # noqa: E402  (beside this file)

    row = {"name": "board notifications", "need": "optional", "found": False, "line": "lem serve --push-test",
           "used_for": "a notification on the owner's phone or computer when something starts to wait for him; a device turns it on from the "
                       "board's \"Waits for you\" (an iPhone from the board added to its Home Screen)"}
    said = lem_push.status()
    if said.get("problem"):
        return [{**row, "detail": said["problem"], "without_it": "no device gets a notification until the file reads"}]
    devices = said["devices"]
    if not devices:
        return [{**row, "detail": "no device has turned them on", "without_it": "the owner learns what waits from the board or a task's session only"}]
    last = said.get("last") or {}
    answers = ", ".join(f"{r.get('device')}: {r.get('status') or 'no answer'}" for r in last.get("results") or [])
    went = f"the last push went at {last['at']} ({answers})" if last.get("at") else "no push has gone yet"
    return [{**row, "found": True, "detail": f"{len(devices)} {'device' if len(devices) == 1 else 'devices'} ({', '.join(d['device'] or '?' for d in devices)}); {went}",
             "without_it": None}]


def plannotator() -> dict:
    # recommended (away-questions-reach-phone, 2026-11-22): while the owner is away, the board's server sends
    # what waits for him to the Inbox (lem_inbox.py), and without it nothing is sent and no step of a task fails
    row = tool("plannotator", "recommended", "the Inbox carries what waits for the owner while he is away, to his phone too, "
               "and brings his answer back into the task's session",
               "nothing goes to the Inbox: while the owner is away, what waits for him waits in the task's session and on the board, "
               "and the phone's page of the task says why there is no Inbox link", "plannotator", ["--version"])
    return {**row, "guide": "https://github.com/backnotprop/plannotator"}


def cronn() -> dict:
    row = tool(
        "cronn", "required", "a scheduled retro and a night run",
        "no retro and no night run starts by itself, so the corrections wait unread; install it from https://cronn.umputun.dev "
        "(a Homebrew formula and an agent that starts at login)", "cronn",
    )
    env_file = Path(os.environ.get("CRONN_CONFIG_DIR") or Path.home() / ".config" / "cronn") / "cronn.env"
    port = None
    try:
        # only the port is read; a line in another encoding is no port
        lines = env_file.read_text(encoding="utf-8", errors="replace").splitlines() if env_file.is_file() else []
    except OSError:
        lines = []
    if lines:
        for line in lines:
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
    # no arguments: `--help` prints the usage, and any other word is a usage error (exit 2), before the check runs
    argparse.ArgumentParser(prog="lem doctor", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    tools = [
        python(),
        tool("git", "required", "worktrees, branches and the task state directory", "nothing runs", "git", ["--version"]),
        tool("revmux", "required", "the review rounds before the pull request, with the project's profiles and lenses",
             "only one read can review a change: a careful or large request, or one after a must-fix, needs a round at the least, "
             "and it is not proposed", "revmux", ["--version"]),
        skill("revmux", "how an agent runs a review round: it writes the round's context and reads the findings back",
              "an agent has the review tool and no instructions for it; install the skill that comes with revmux (its README says how)"),
        *agterm(),
        gh(),
        # The recipes of the agterm cookbook that Lem needs: none is copied into Lem, and each has
        # the guide the developer installs it by.
        skill("webrev", "the owner marks up a plan, a draft or any document as a rendered page, and the notes come back to the agent",
              "Lem cannot open a plan or a document for the owner to mark up; install the recipe from its guide",
              guide=COOKBOOK + "annotate-document"),
        # agdoc: no step of Lem makes its page since the merge agent's `merge-review.md` took the place of
        # the owner's page of a task (the owner's ruling of 2026-11-20, AGENTS.md), so it is recommended
        skill("agdoc", "a page about an issue, a plan or a change that the owner asks for himself, to read in agterm",
              "no step of Lem needs it; the owner has no page of his own to ask for", need="recommended", guide=COOKBOOK + "html-doc-overlay"),
        skill("backlog", "the owner's own view of the backlog items in docs/backlog/, and the picker that adds and opens them",
              "the owner has no tool of his own for the backlog; install the recipe from its guide, for the user (~/.claude/skills/backlog) "
              "or for this repository (.claude/skills/backlog)", guide=COOKBOOK + "backlog-picker"),
        # A recommended tool: Lem installs it only on the developer's yes.
        {**tool("plannotator-tui", "recommended", "the owner marks up what a pane printed, or an agent's newest reply, from two agterm chords",
                "no stage needs it", "plannotator-tui", ["--version"]), "guide": COOKBOOK + "annotate-in-plannotator-tui"},
        plannotator(),
        jev_key(),
        *codex(),
        *claude(),
        tool("mailbox-chat", "required", "the wake-up of a task's idle session by the board's server (a merge, a conflict, its turn in the queue) rests on its "
             "waiter, the owner's hook; and the messages between the defender and the reviewer of a plan talk",
             "an idle task session never hears a merge or a conflict, and the two agents of a plan talk cannot talk; install agterm's two-agent mailbox chat "
             "recipe from its cookbook, which puts mailbox-chat.py on PATH", "mailbox-chat.py"),
        skill("mailbox-chat", "how an agent sends to the other pane and reads what comes back",
              "an agent has the command and no instructions for it; the same recipe of agterm's cookbook installs the skill"),
        cronn(),
        load_gate(),
        handoff_tokens(),
        *board_server(),
        *installed_lem(),
        *board_notifications(),
        *project(),
        *correction_hook(),
        *permission_mode(),
        *user_plugin(),
    ]
    ok = all(row["found"] for row in tools if row["need"] == "required")
    print(json.dumps({"ok": ok, "tools": tools}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

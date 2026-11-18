#!/usr/bin/env python3
"""Say which of the tools Lem uses this machine has.

Onboarding runs it first, so a repository is never set up for a flow its machine cannot run. It
prints one row per tool as JSON and exits 1 when a required one is absent. An optional tool that
is absent is not an error: its row says what the skill does without it, and onboarding tells the
owner that. A recipe of the agterm cookbook that Lem needs (webrev, agdoc, the backlog) is
required, and its row has the guide to install it by. A recommended tool is one Lem does not bring
and a developer is better off with: its row has the guide too, and Lem installs it only on the
developer's yes. Four rows
are about the repository it runs in and never fail the check: its personas, the correction hook
when more than one place registers it there, the permission mode a builder in the background
meets there, and Lem's plugin when it is installed for the user and so loads in every repository.

    lem doctor

It loads under an old `python3` too, so that a machine whose first `python3` is the one its system
ships gets a row that says so, not a traceback.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
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
    return {
        "name": "python3", "need": "required", "found": sys.version_info >= (3, 11), "detail": f"{sys.version.split()[0]} at {sys.executable}",
        "used_for": "every script of Lem; the settings file is read with a module that came with Python 3.11",
        "without_it": "no script of Lem runs; put a python3 of 3.11 or newer first on PATH",
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


# The correction hook in a settings file, in any form: the one an install of Lem before the plugin
# wrote (`python3 /PATH/corrections.py hook`, with a timeout of 10), or one added by hand.
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

    The hook comes with Lem's plugin. A second place is a settings file that still holds the hook
    an install of Lem before the plugin wrote there, and no command of Lem's takes it out: the
    guide names each entry to delete by hand. Its need is `project`, as the personas' row: it is
    about what this repository gets, and it never fails the machine check. The hook judges each
    message once however often it starts, so the row is about telling the truth, not about a
    wrong queue.
    """
    roots = checkout_roots()
    places = hook_places(Path.home(), roots[0] if roots else None)
    if len(places) < 2:
        return []
    extra = [place for place in places if place["remove"] is not None]
    if len(extra) < len(places):
        fix = "The plugin brings the hook, so remove each other place: " + "; ".join(f"{place['where']}: {place['remove']}" for place in extra)
    else:
        # no plugin among them: the settings files are all an older install's, and the plugin is what brings the hook now
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
    """A skill an agent loads by name: in a skills folder of the home or of this repository, or installed as a plugin of Claude Code."""
    places = [base / home / name for base in [*checkout_roots(), Path.home()] for home in SKILL_HOMES]
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


def gh() -> dict:
    """The GitHub CLI: found or not, and signed in or not. The row is optional, since a project with
    no GitHub remote, or with `branch.propose = "merge"`, never calls it."""
    row = tool(
        "gh", "optional", "the pull request of each task and the watch of the open ones, where the remote is GitHub",
        "with a GitHub remote `lem land propose` and the watch stop and say so; install the GitHub CLI and run `gh auth login`", "gh", ["--version"],
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
        "agterm", "required", "the reviewer's pane, pages for the owner, and the companion of a plan talk",
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
    return [row, skill] if row["found"] else [row]


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
    row = tool("codex", "optional", "a reviewer of another model family, the second expert of a choice, and half of each persona panel",
               "the reviewer is a second Claude; an expert whose seat names codex (the second of seats.experts by default, GPT-6 Astra) "
               "does not answer, so a choice that waits for the owner gets one expert's advice and, when his wait ends, the recommended "
               "option, and its pull request is not green for it; a persona panel has the answers of one model family, so a split "
               "between two is not seen", "codex", ["--version"])
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
    "default": "each command the allow list does not hold asks for permission, and the question comes up in Lem's session, so the task waits; at night nobody answers",
    "acceptEdits": "an edit goes through, and each other command the allow list does not hold asks for permission in Lem's session, so the task waits; at night nobody answers",
    "plan": "a builder can read and cannot edit or commit, so no task builds",
    "dontAsk": "each command the allow list does not hold is refused with no question, so a builder stops at the first one",
}


def permission_mode() -> list[dict]:
    """In a repository: the permission mode a new session starts in there, and what a builder in the
    background meets in it. No row outside a repository. The repository's local settings say it
    first, then its shared ones, then the user's; `auto` and `bypassPermissions` count only from the
    user's. Its need is `project`, as the personas' row: it never fails the machine check."""
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
    meets = MODE_SAYS.get(mode, "a mode this check does not know; a builder may ask for permission in Lem's session")
    return [{
        "name": "permission mode", "need": "project", "found": silent,
        "detail": f"{mode}, from {source}" if source else "default: no settings file names one",
        "used_for": "the builders and the leads, which run in the background: a command that asks for permission stops the task until someone answers in Lem's session",
        "without_it": (
            "a builder asks nobody" + ("; the classifier may still refuse a step, which the owner then runs himself" if mode == "auto" else "")
            if silent else
            f"{meets}. "
            "The allow list that /lem init proposes for the repository's .claude/settings.json holds Lem's commands, git's and the checks', "
            "so that a builder asks for none of them; `auto` or `bypassPermissions` in the user's settings asks for nothing"
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
            "the skills and the hook load in every repository; the hook in a repository with no .lem/project.toml writes nothing and costs "
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
        "cronn", "required", "a scheduled retro, a night plan, and the agents' free hours",
        "no retro and no night plan starts by itself, so the corrections wait unread; install it from https://cronn.umputun.dev "
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
        skill("agdoc", "a page about the issue, the plan or the change in hand, for the owner's own reading",
              "Lem cannot make a page for the owner to read; install the recipe from its guide", guide=COOKBOOK + "html-doc-overlay"),
        skill("backlog", "the owner's own view of the backlog items in docs/backlog/, and the picker that adds and opens them",
              "the owner has no tool of his own for the backlog; install the recipe from its guide, for the user (~/.claude/skills/backlog) "
              "or for this repository (.claude/skills/backlog)", guide=COOKBOOK + "backlog-picker"),
        # The recommended tool: Lem installs it only on the developer's yes.
        {**tool("plannotator-tui", "recommended", "the owner marks up what a pane printed, or an agent's newest reply, from two agterm chords",
                "no stage needs it", "plannotator-tui", ["--version"]), "guide": COOKBOOK + "annotate-in-plannotator-tui"},
        {
            "name": "OpenRouter key", "need": "optional", "found": bool(os.environ.get("OPENROUTER_API_KEY")), "detail": None,
            "used_for": "the Jev decision model, which the correction queue and a card's framing check ask",
            "without_it": "neither gets an answer, and the correction hook logs each message as a failure; "
                          "put OPENROUTER_API_KEY into the environment the agent starts with",
        },
        *codex(),
        *claude(),
        tool("mailbox-chat", "required", "messages between Lem and a task's lead, and between the defender and the reviewer of a plan talk",
             "the two agents cannot talk; install agterm's two-agent mailbox chat recipe from its cookbook, which puts mailbox-chat.py on PATH", "mailbox-chat.py"),
        skill("mailbox-chat", "how an agent sends to the other pane and reads what comes back",
              "an agent has the command and no instructions for it; the same recipe of agterm's cookbook installs the skill"),
        cronn(),
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

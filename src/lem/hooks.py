"""The one entry of the plugin's hooks: `lem-hook SELECTOR` (pyproject.toml,
`[project.scripts]`), which `hooks/run` of the plugin starts with the hook's event on
stdin.

    corrections      UserPromptSubmit: the correction hook (`corrections.cmd_hook`)
    serve            SessionStart: the start of the board server (`serve_hook`)
    session-start    SessionStart: a task's session's records (`session_hook`), and the
                     two checks below
    precompact       PreCompact: a task's compaction summary's form (`session_hook`)
    stop             Stop: lem-ask's status at the end of a turn (`ask.hook_stop`)

A hook never fails a session. Whatever goes wrong, a selector of no handler, a package
that is not whole (`paths` stops with SystemExit), a handler that raises or exits other
than 0, ends in exit 0 with nothing on stdout or stderr: Claude Code takes a hook's
output as context, and a PreCompact hook's exit 2 blocks the compaction. A handler's
output is held while it runs and printed only when it ended well. This file imports
nothing of the command line, and nothing of the package at its top: a handler's module
is imported when its selector runs (`test_hooks.HookStart` holds each selector to its
handler's own imports, and `lem doctor`'s row `hook modules` reads that this file has no
import of the package at its top).

The plugin Claude Code loaded (`CLAUDE_PLUGIN_ROOT`) and this app are two installs that
each have a version, in `.claude-plugin/plugin.json`. When the two differ, every hook
but `session-start` does nothing and says nothing; `session-start` says one line, as a
`systemMessage`, that names the one that is behind and its update command
(`version_line`). It also writes `export LEM_PLUGIN_ROOT=...` into the file
`CLAUDE_ENV_FILE` names, which the session's Bash tool runs before each command, so that
a command `lem` of that session stops with the same line (`__main__.cli`). With no
`CLAUDE_PLUGIN_ROOT` there is no check. `session-start` also says one line when the
first `lem` on its PATH is another file than this app's own command (`other_lem`),
which it compares by identity and never runs. Claude Code's hooks reference, read
2026-11-25: a SessionStart hook's plain stdout is context for Claude, and
`systemMessage` of a hook's JSON is a warning shown to the user; `CLAUDE_ENV_FILE` is
given to SessionStart hooks, which append `export` lines to it.
"""

import os
import sys

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable


# What the app is, by the rule of `paths.root`, in `os.path` alone: pathlib is a cost a
# hook that does nothing must not pay. The data folder in an installed app; else the
# checkout this package is part of, when it holds the skill `lem`; else None.
HERE = os.path.dirname(os.path.realpath(__file__))
MANIFEST = os.path.join(".claude-plugin", "plugin.json")
# The update command of each half, for the line that names the one that is behind.
APP_UPDATE = "brew upgrade pySilver/tap/lem"
PLUGIN_UPDATE = "claude plugin update lem@lem"


def app_root() -> str | None:
    """`paths.ROOT` of this app, or None where `paths` would stop."""
    data = os.path.join(HERE, "data")
    if os.path.isdir(data):
        return data
    checkout = os.path.dirname(os.path.dirname(HERE))
    if os.path.isfile(os.path.join(checkout, "skills", "lem", "SKILL.md")):
        return checkout
    return None


def numbers(version: object) -> tuple[int, ...] | None:
    """`0.3.1` as (0, 3, 1); None for a version that is not numbers joined by dots."""
    if not isinstance(version, str) or not version:
        return None
    parts = version.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def manifests(files: tuple[str, str]) -> list[bytes] | str:
    """The bytes of the plugin's manifest and the app's, FILES; or the one line that
    names the one that does not read."""
    read = []
    for file, fix in zip(
        files, ("installs Lem's plugin again", "installs Lem again"), strict=True
    ):
        try:
            with open(file, "rb") as manifest:
                read.append(manifest.read())
        except OSError as error:
            return (
                f"lem: {file} does not read ({error.strerror}), so Lem cannot tell "
                f"whether its plugin and its app are one version; the owner {fix}"
            )
    return read


def versions(files: tuple[str, str], read: list[bytes]) -> list[str] | str:
    """The versions the manifests FILES name, from their bytes READ; or the one line
    that names the one that names none."""
    import json

    found = []
    for file, text in zip(files, read, strict=True):
        try:
            manifest = json.loads(text)
        except ValueError:
            manifest = None
        version = manifest.get("version") if isinstance(manifest, dict) else None
        if not isinstance(version, str) or not version:
            return (
                f"lem: {file} names no version, so Lem cannot tell whether its "
                "plugin and its app are one version; the owner installs that half again"
            )
        found.append(version)
    return found


def version_line(plugin: str, app: str) -> str | None:
    """The one line that says the plugin at PLUGIN and the app at APP (each a folder
    with `.claude-plugin/plugin.json`) are of two versions, and which one is behind with
    its update command; None when they are one version. A manifest that does not read
    is named by its file. Two files of the same bytes are one version, with no parse."""
    files = (os.path.join(plugin, MANIFEST), os.path.join(app, MANIFEST))
    read = manifests(files)
    if isinstance(read, str):
        return read
    if read[0] == read[1]:
        return None
    found = versions(files, read)
    if isinstance(found, str):
        return found
    theirs, mine = found
    return None if theirs == mine else behind(plugin, app, theirs, mine)


def behind(plugin: str, app: str, theirs: str, mine: str) -> str:
    """The line for the plugin at PLUGIN of the version THEIRS and the app at APP of
    the version MINE, two versions: the one that is behind, with its update command."""
    plugin_numbers, app_numbers = numbers(theirs), numbers(mine)
    if plugin_numbers is None or app_numbers is None:
        return (
            f"lem: Lem's plugin {theirs} ({plugin}) and Lem's app {mine} ({app}) are "
            f"two versions; the owner runs `{APP_UPDATE}` and `{PLUGIN_UPDATE}`, and "
            "starts the session again"
        )
    if plugin_numbers < app_numbers:
        return (
            f"lem: Lem's plugin {theirs} ({plugin}) is behind Lem's app {mine}; "
            f"the owner runs `{PLUGIN_UPDATE}` and starts the session again"
        )
    return (
        f"lem: Lem's app {mine} ({app}) is behind Lem's plugin {theirs}; "
        f"the owner runs `{APP_UPDATE}` and starts the session again"
    )


def runnable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def same_file(one: str, other: str) -> bool:
    """Whether the two paths are one file, after their links; False when one is not
    there."""
    try:
        return os.path.samefile(os.path.realpath(one), os.path.realpath(other))
    except OSError:
        return False


def other_lem(search: str, own: str) -> str | None:
    """The one line that says the first `lem` on the search path SEARCH is another file
    than OWN, this app's command, and which folder must come before its folder; None
    when no `lem` is on SEARCH, when it is OWN, or when OWN is not there. Neither is
    run."""
    folders = [folder for folder in search.split(os.pathsep) if folder]
    first = next(
        (
            os.path.join(folder, "lem")
            for folder in folders
            if runnable(os.path.join(folder, "lem"))
        ),
        None,
    )
    if first is None or not runnable(own) or same_file(first, own):
        return None
    mine = next(
        (folder for folder in folders if same_file(os.path.join(folder, "lem"), own)),
        os.path.dirname(own),
    )
    return (
        f"lem: {first} comes first on PATH, and it is not Lem's command {own}; "
        f"the owner puts {mine} before {os.path.dirname(first)} in his PATH"
    )


def own_command() -> str:
    """This app's command `lem`: the one beside the interpreter that runs this hook."""
    return os.path.join(os.path.dirname(sys.executable), "lem")


def keep_root(plugin: str) -> None:
    """Append `export LEM_PLUGIN_ROOT='PLUGIN'` to the file CLAUDE_ENV_FILE names, when
    it names one: the session's Bash tool runs that file before each command."""
    target = os.environ.get("CLAUDE_ENV_FILE", "")
    if not target:
        return
    quoted = "'" + plugin.replace("'", "'\\''") + "'"
    try:
        with open(target, "a", encoding="utf-8") as out:
            out.write(f"export LEM_PLUGIN_ROOT={quoted}\n")
    except OSError:
        # the session's commands then run with no check, as in a plain shell
        return


# selector -> the module of this package and its function that handles it; a module is
# imported when its selector runs
HANDLERS = {
    "corrections": ("corrections", "cmd_hook"),
    "serve": ("serve_hook", "main"),
    "session-start": ("session_hook", "main"),
    "precompact": ("session_hook", "main"),
    "stop": ("ask", "hook_stop"),
}


def handler(selector: str) -> Callable[[], None]:
    """The function that handles SELECTOR, with its module imported."""
    module, function = HANDLERS[selector]
    name = f"lem.{module}"
    # __import__, not importlib: no module more at a hook's start
    __import__(name)
    return getattr(sys.modules[name], function)


def held(work: Callable[[], None]) -> str | None:
    """Run WORK with its stdout and stderr held; what it printed on stdout when it
    ended well (returned, or exited 0), else None."""
    import io

    out, err = sys.stdout, sys.stderr
    buffer = io.StringIO()
    sys.stdout, sys.stderr = buffer, io.StringIO()
    try:
        work()
    except SystemExit as stopped:
        well = stopped.code in (None, 0)
    except BaseException:  # noqa: BLE001 - a hook that fails must not fail the session
        well = False
    else:
        well = True
    finally:
        said = buffer.getvalue()
        sys.stdout, sys.stderr = out, err
    return said if well else None


def run(selector: str) -> str:
    """What the hook SELECTOR prints: its handler's output when it ended well, and
    nothing when the plugin and the app are two versions, but for `session-start`,
    which says so: see the module's text."""
    if selector not in HANDLERS:
        return ""

    def work() -> None:
        # the import too is held: a package that is not whole stops in it
        handler(selector)()

    plugin = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    app = app_root()
    behind = version_line(plugin, app) if plugin and app else None
    if selector != "session-start":
        return "" if behind else held(work) or ""
    if plugin:
        keep_root(plugin)
    lines = [
        line
        for line in (behind, other_lem(os.environ.get("PATH", ""), own_command()))
        if line
    ]
    said = "" if behind else held(work) or ""
    if not lines:
        return said
    import json

    shown: dict[str, object] = {"systemMessage": "\n".join(lines)}
    if said.strip():
        # the task's context, which plain stdout gives when there is no line to say
        shown["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": said,
        }
    return json.dumps(shown, ensure_ascii=False) + "\n"


def cli() -> None:
    """The command `lem-hook SELECTOR`: see the module's text."""
    try:
        said = run(sys.argv[1] if len(sys.argv) > 1 else "")
        if said:
            sys.stdout.write(said)
            sys.stdout.flush()
    except BaseException:  # noqa: BLE001, S110 - a hook that fails must not fail the session
        pass
    # not sys.exit: a flush at the interpreter's exit that fails would print on stderr
    os._exit(0)

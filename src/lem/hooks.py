"""The one entry of the plugin's hooks: `lem-hook SELECTOR` (pyproject.toml,
`[project.scripts]`), which `hooks/run` of the plugin starts with the hook's event on
stdin.

    corrections      UserPromptSubmit: the correction hook (`corrections.cmd_hook`)
    serve            SessionStart: the start of the board server (`serve_hook`)
    session-start    SessionStart: a task's session's records (`session_hook`)
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
"""

import os
import sys

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable


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
    """What the hook SELECTOR prints: its handler's output when it ended well, else
    nothing."""
    if selector not in HANDLERS:
        return ""

    def work() -> None:
        # the import too is held: a package that is not whole stops in it
        handler(selector)()

    return held(work) or ""


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

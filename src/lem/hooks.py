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
nothing of the command line, and nothing a handler does not need: each handler's module
is imported in its own function (`test_hooks.HookStart` holds each selector to its
handler's own imports).
"""

import os
import sys

# typing's flag, without the import of typing, which a hook's start does not pay
TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable


def corrections() -> None:
    from lem import corrections as lem_corrections

    lem_corrections.cmd_hook()


def serve() -> None:
    from lem import serve_hook

    serve_hook.main()


def session() -> None:
    from lem import session_hook

    session_hook.main()


def stop() -> None:
    from lem import ask

    ask.hook_stop()


# selector -> its handler
HANDLERS = {
    "corrections": corrections,
    "serve": serve,
    "session-start": session,
    "precompact": session,
    "stop": stop,
}


def held(handler: Callable[[], None]) -> str | None:
    """Run HANDLER with its stdout and stderr held; what it printed on stdout when it
    ended well (returned, or exited 0), else None."""
    import io

    out, err = sys.stdout, sys.stderr
    buffer = io.StringIO()
    sys.stdout, sys.stderr = buffer, io.StringIO()
    try:
        handler()
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
    handler = HANDLERS.get(selector)
    if handler is None:
        return ""
    return held(handler) or ""


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

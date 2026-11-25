"""The command `lem-hook SELECTOR`: the plugin's hooks, on the standard library only.

    corrections      UserPromptSubmit: the owner's message, for the correction queue
    serve            SessionStart (startup, resume): the board server's start, detached
    session-start    SessionStart (every source): the task's session on record, the plugin's
                     folder for the session's commands, the version line, the other `lem`
    precompact       PreCompact: the form of a task's compaction summary
    stop             Stop, async: the mark of an open card

`hooks/run` starts it with the hook's event on stdin, and passes its output on only when it
exited 0: a hook that fails says nothing and never fails the session. A selector's module is
imported only when it runs. When the plugin Claude Code loaded (`CLAUDE_PLUGIN_ROOT`) and this app
are two versions, every selector but `session-start` does nothing and says nothing, and
`session-start` says the one line that names the half behind.
"""

import importlib
import os
import sys

from lem.hooks import versions

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping

# Each selector and the module that answers it with `answer(environ, behind) -> str`.
SELECTORS = (
    ("corrections", "lem.hooks.corrections"),
    ("serve", "lem.hooks.serve"),
    ("session-start", "lem.hooks.session"),
    ("precompact", "lem.hooks.precompact"),
    ("stop", "lem.hooks.stop"),
)
# Every failure a hook's work can raise, written out: an `Exception` caught whole is refused by
# the gates, and `contextlib.suppress` costs an import that every hook would pay.
FAILURES = (
    ArithmeticError,
    AttributeError,
    ImportError,
    LookupError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)
# The one selector that runs, and says so, when the plugin and the app are two versions.
SAYS_BEHIND = "session-start"


def run(selector: str, environ: Mapping[str, str]) -> str:
    """What the hook `selector` prints: nothing for a selector Lem has not, nothing from an
    app whose own files are not whole (it cannot tell its version), and nothing but the version
    line when the plugin and the app are two versions."""
    module = dict(SELECTORS).get(selector)
    app = versions.app_root()
    if module is None or app is None:
        return ""
    plugin = environ.get("CLAUDE_PLUGIN_ROOT", "")
    behind = versions.behind(plugin, app) if plugin else None
    if behind and selector != SAYS_BEHIND:
        return ""
    return importlib.import_module(module).answer(environ, behind)


def main() -> None:
    """Answer the hook that the first argument names, on its event, and exit 0 whatever
    happens: a hook that fails says nothing, and a session never fails on one. `os._exit`,
    not `sys.exit`: a flush at the interpreter's exit that fails would print on stderr."""
    selector = "".join(sys.argv[1:2])
    try:
        said(run(selector, os.environ))
    except FAILURES:
        os._exit(0)
    os._exit(0)


def said(words: str) -> None:
    """Print the hook's words, whole."""
    sys.stdout.write(words)
    sys.stdout.flush()

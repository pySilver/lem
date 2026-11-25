"""The `stop` hook, async: it reads no input, so a pipe that stays open never keeps it alive, and it
says nothing at a turn's end. The mark of an open card, rechecked, is the step `ask`'s."""

import subprocess
import tempfile

from hooks.claude_code import LINES, claude_environ
from lem.hooks import raw

# How long the stop hook may take with its input never closed, in seconds: under `raw.WAIT`,
# the most a hook that reads its event waits for it, so a stop hook that read it would fail here.
ENDS_WITHIN = raw.WAIT * 0.75


def test_a_stdin_that_stays_open_does_not_keep_the_stop_hook_alive() -> None:
    child = subprocess.Popen(
        ["/bin/sh", "-c", LINES["stop"]],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=claude_environ({}),
        cwd=tempfile.gettempdir(),
    )
    try:
        assert child.wait(timeout=ENDS_WITHIN) == 0
        assert child.stdout is not None
        assert child.stdout.read() == b""
    finally:
        assert child.stdin is not None
        child.stdin.close()
        if child.poll() is None:
            child.kill()
            child.wait()

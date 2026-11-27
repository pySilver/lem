"""The command `lem`: the version check, then the command tree on the arguments it was given.

`help` and `version` answer first, and `doctor` and `uninstall` whatever the versions.
The first word is read past the root's `--repo PATH`. In a session whose
`session-start` hook named Lem's plugin in `LEM_PLUGIN_ROOT`, every other command refuses with
the one line that names the half that is behind, when the plugin and this app are two versions
(the design's part 5). Then it starts the board server when none lives (`board/look.py`).
"""

import os
import sys
from typing import TYPE_CHECKING

import msgspec

from lem.board import look
from lem.cli import lazy
from lem.hooks import versions
from lem.kernel import paths
from lem.kernel.envelope import Envelope, Refused

if TYPE_CHECKING:
    from collections.abc import Mapping

# The commands that answer whatever the plugin's version.
UNCHECKED = ("help", "--help", "-h", "version", "doctor", "uninstall")


def first_word(argv: list[str]) -> str | None:
    """The command's first word, past the root's `--repo PATH` or `--repo=PATH`."""
    words = list(argv)
    if words and words[0] == "--repo":
        words = words[2:]
    elif words and words[0].startswith("--repo="):
        words = words[1:]
    return words[0] if words else None


def refusal(argv: list[str], environ: Mapping[str, str]) -> Envelope | None:
    """The refusal of a command whose session loaded a plugin of another version."""
    plugin = environ.get("LEM_PLUGIN_ROOT", "")
    first = first_word(argv)
    if not plugin or first is None or first in UNCHECKED:
        return None
    line = versions.behind(plugin, str(paths.root()))
    if line is None:
        return None
    refused = Refused(
        code="version",
        why=line,
        fix="the owner updates the half that is behind and starts the session again",
    )
    return Envelope(ok=False, refusal=refused)


def main() -> None:
    """Run the command the arguments name, and exit with its code."""
    argv = sys.argv[1:]
    refused = refusal(argv, os.environ)
    if refused is not None:
        sys.stdout.buffer.write(msgspec.json.encode(refused))
        sys.stdout.buffer.write(b"\n")
        sys.exit(1)
    first = first_word(argv)
    if first in dict(lazy.ROOT.table):
        look.looked(first, os.environ)
    sys.exit(lazy.main(argv))


if __name__ == "__main__":
    main()

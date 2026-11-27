"""Lem's own allow rules in Claude Code's settings files: `Bash(lem *)` and the `Read(...)` rule
that `lem doctor` gives, matched exactly, and taken out of `permissions.allow` with every other
key of the file kept.

A settings file that is a link is written through it, so the link stays.
"""

import os
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.claude_plugin import claude_home
from lem.cli.doctor import reads
from lem.kernel import files, folders

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from lem.cli.doctor.look import Look
    from lem.cli.uninstall.report import Report

SHELL = "Bash(lem *)"

type Rules = tuple[str, ...]
type Table = dict[str, object]


def own(look: Look) -> Rules:
    """The two rules Lem gives the owner."""
    return SHELL, reads.read_line(look)


def table(path: Path) -> Table:
    """The JSON object of a settings file; empty when there is no file, refused when it does
    not read as one."""
    folders.inside_test_root(path)
    try:
        return msgspec.json.decode(path.read_bytes(), type=dict[str, object])
    except FileNotFoundError:
        return {}


def kept(settings: Table, rules: Rules) -> list[object] | None:
    """The allow list without `rules`; None when it holds none of them."""
    permissions = settings.get("permissions")
    allow = permissions.get("allow") if isinstance(permissions, dict) else None
    if not isinstance(allow, list):
        return None
    left = [rule for rule in allow if rule not in rules]
    return left if len(left) < len(allow) else None


def holding(roots: Iterable[Path], rules: Rules) -> tuple[Path, ...]:
    """The settings files that hold one of `rules`: the user's, and the local one of each
    repository of `roots`."""
    user = claude_home(os.environ) / "settings.json"
    local = (root / ".claude" / "settings.local.json" for root in roots)
    return tuple(
        path for path in (user, *local) if kept(table(path), rules) is not None
    )


def taken_out(path: Path, rules: Rules, report: Report) -> None:
    """Take `rules` out of the file, read again now, since Claude Code may have written it."""
    with report.step(
        f"the allow rules in {path}", f"the owner checks the JSON of {path}"
    ):
        settings = table(path)
        left = kept(settings, rules)
        if left is None:
            return
        permissions = settings["permissions"]
        if isinstance(permissions, dict):
            permissions["allow"] = left
        body = msgspec.json.format(msgspec.json.encode(settings), indent=2)
        files.write_whole(path.resolve(), b"%b\n" % body)
        report.gone(f"Lem's allow rules in {path}")

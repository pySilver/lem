"""The folder a call of `lem` starts from: `--repo PATH` before the noun, else the working one.

One option of the root, so that a builder in another folder runs `lem --repo WORKTREE NOUN ...`
under the one permission rule `Bash(lem *)`, where `cd WORKTREE && lem ...` would need another.
This module gives the starting folder only: which checkout is the main one, and where its
`.lem/` is, is the job of the steps that read the workspace
(`docs/plans/2026-11-25-lem-built-again/notes/tree.md`).
"""

from pathlib import Path

import click

OPTION = click.Option(
    ["--repo"],
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
    help="run the command for the repository this folder is in (default: the working one)",
)


def folder(default: Path | None = None) -> Path:
    """The folder `--repo` named, else the command's default or working directory."""
    ctx = click.get_current_context(silent=True)
    if ctx is None:
        return default or Path.cwd()
    named = ctx.find_root().params.get("repo")
    return named if isinstance(named, Path) else default or Path.cwd()

"""Everything `lem uninstall` reads before it asks the owner: the repositories and their open
tasks, the scopes of the plugin and the marketplace, the settings files that hold Lem's allow
rules, and the cronn jobs that run Lem.

An open task refuses the whole run before anything else is read; a read of Claude Code or of
cronn that fails is a failed step of the report, and the steps that do not need it still run.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.cli.ask import temp_pages
from lem.cli.doctor import look
from lem.cli.uninstall import claude, cronn, repos, rules
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.adapters.git_cli import GitCli
    from lem.cli.uninstall.report import Report


class Found(msgspec.Struct, frozen=True, kw_only=True):
    """What the run removes, keeps and leaves for the owner."""

    home: Path
    pages: Path
    repos: tuple[repos.Repo, ...]
    plugins: tuple[claude.Scope, ...] = ()
    markets: tuple[claude.Scope, ...] = ()
    rules: tuple[str, ...] = ()
    holders: tuple[Path, ...] = ()
    jobs: tuple[cronn.Job, ...] | None = None
    jobs_file: Path | None = None


def gathered(git: GitCli, report: Report, *, force: bool) -> Found:
    """Read everything; refused while a task is open and the owner did not say `--force`."""
    home = paths.home(os.environ)
    listed = repos.listed(home, git)
    repos.guarded(listed, force=force)
    seen = look.looked(os.environ, Path.cwd())
    roots = tuple(one.root for one in listed)
    plugins = report.tried(
        "Claude Code's plugins", lambda: claude.installs(seen.home), ()
    )
    return Found(
        home=home,
        pages=temp_pages.folder(),
        repos=listed,
        plugins=plugins,
        markets=report.tried(
            "Claude Code's marketplaces",
            lambda: claude.markets(seen.home, roots, plugins),
            (),
        ),
        rules=rules.own(seen),
        holders=report.tried(
            "Lem's allow rules", lambda: rules.holding(roots, rules.own(seen)), ()
        ),
        jobs=report.tried("cronn's jobs", lambda: cronn.lem_jobs(seen), None),
        jobs_file=cronn.jobs_file(seen),
    )


def unchanged(git: GitCli, found: Found) -> bool:
    """Whether the repositories and their open tasks are as they were when the owner read
    them."""
    now = repos.listed(found.home, git)
    return [(one.root, one.open) for one in now] == [
        (one.root, one.open) for one in found.repos
    ]

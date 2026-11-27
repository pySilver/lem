"""`lem uninstall`: remove what Lem put on this computer, in the order a person undoes it.

    lem uninstall [--yes] [--force]

It reads everything first, lists it, and asks the owner once: `yes` keeps each repository's
`.lem/state/` and `.lem/worktrees/`, `all` removes them too. `--yes` takes `yes` with no
question; with no one at the terminal and no `--yes` it refuses. An open task refuses it, unless
`--force`, which keeps that task's worktree, its branch and its repository's state. Then it stops
the board server and closes the tailnet door, removes the plugin and the marketplace from each
scope, takes Lem's allow rules out, names the cronn jobs that run Lem for the owner to delete,
cleans each repository, and last removes Lem's home folder and `$TMPDIR/lem-ask/`. The home
folder stays when a step failed, so that the next run finds the repositories again. It removes
no app: it ends with the `brew` line that does.
"""

import os

import click
import msgspec

from lem.adapters.claude_plugin import PLUGIN
from lem.adapters.git_cli import GitCli
from lem.cli.uninstall import claude, computer, cronn, preview, repos, rules
from lem.cli.uninstall.found import Found, gathered, unchanged
from lem.cli.uninstall.report import Report, ended
from lem.kernel.errors import Refusal

DECLINED = "no"
KEEPS = "yes"
ALL = "all"


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem uninstall`: `unasked` is `--yes`."""

    unasked: bool = False
    force: bool = False


def answer(call: Call, found: Found) -> str:
    """The list, then the owner's one answer: `yes`, `all`, or a refusal on `no`."""
    for line in preview.lines(found):
        click.echo(line, err=True)
    if call.unasked:
        return KEEPS
    words = (DECLINED, KEEPS, ALL) if found.repos else (DECLINED, KEEPS)
    try:
        said = click.prompt(
            "Remove this? yes keeps each .lem/state/ and .lem/worktrees/, all removes them",
            default=DECLINED,
            type=click.Choice(words),
            err=True,
        )
    except click.Abort:
        said = DECLINED
    if said == DECLINED:
        raise Refusal(
            "uninstall-no",
            "the owner said no, and nothing was removed",
            "the owner runs lem uninstall again to remove Lem",
        )
    return said


def removed_claude(found: Found, report: Report) -> None:
    """The plugin from each of its scopes, then the marketplace it comes from, only when
    every install of the plugin went."""
    failed = len(report.failed)
    for scope in found.plugins:
        claude.removed(("plugin", "uninstall", PLUGIN), scope, report)
    for scope in found.markets:
        if len(report.failed) > failed:
            report.stays(f"the marketplace {claude.MARKET} of {scope.said}")
        else:
            claude.removed(
                ("plugin", "marketplace", "remove", claude.MARKET), scope, report
            )


def removed(git: GitCli, found: Found, report: Report, *, remove: bool) -> None:
    """Each step in its order, the home folder last; it stays when a step failed."""
    stopped = computer.stopped(report)
    computer.door_closed(found.home, report)
    removed_claude(found, report)
    for path in found.holders:
        rules.taken_out(path, found.rules, report)
    cronn.left(found.jobs or (), found.jobs_file, report)
    for repo in found.repos:
        repos.cleaned(git, repo, report, remove=remove and stopped)
    if report.failed:
        report.stays(f"{found.home}, for the run that finishes the rest")
    else:
        computer.removed(found.home, report)
    computer.removed(found.pages, report)


def run(call: Call) -> Report:
    """Read, ask once, then remove."""
    if not call.unasked and not os.isatty(0):
        raise Refusal(
            "uninstall-unattended",
            "lem uninstall asks the owner once, and no one answers at this terminal",
            "the owner runs lem uninstall in a terminal, or lem uninstall --yes, which keeps "
            "each repository's .lem/state/ and .lem/worktrees/",
        )
    git = GitCli(environ=os.environ)
    report = Report()
    found = gathered(git, report, force=call.force)
    remove = answer(call, found) == ALL
    if not unchanged(git, found):
        raise Refusal(
            "uninstall-changed",
            "the repositories or their open tasks changed while the question was open",
            "the owner runs lem uninstall again and reads the new list",
        )
    removed(git, found, report, remove=remove)
    return ended(report)


COMMAND = click.Command(
    "uninstall",
    params=[
        click.Option(
            ["--yes", "unasked"],
            is_flag=True,
            help="answer yes with no question: keep each .lem/state/ and .lem/worktrees/",
        ),
        click.Option(
            ["--force"],
            is_flag=True,
            help="go on with open tasks: keep their worktrees, branches and state",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Remove what Lem put on this computer, after one question to the owner.",
)

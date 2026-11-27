"""What `lem uninstall` removed, what it kept, what it leaves for the owner, and each step that
failed with its fix; each is said on standard error as the step ends.

A step that fails is one entry of `failed`, and the steps that do not need it still run; a run
with a failed step ends as a refusal whose result is this report.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING

import click
import msgspec

from lem.cli import output
from lem.kernel.envelope import Envelope, Refused
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

BREW = "brew uninstall pySilver/tap/lem"
CODE = "uninstall"


class Report(msgspec.Struct, kw_only=True):
    """The outcome of a run, step by step."""

    removed: list[str] = msgspec.field(default_factory=list)
    kept: list[str] = msgspec.field(default_factory=list)
    left_for_owner: list[str] = msgspec.field(default_factory=list)
    failed: list[Refused] = msgspec.field(default_factory=list)

    @contextmanager
    def step(self, subject: str, fix: str) -> Generator[None]:
        """Run one step: a refusal or an error in it is a failed entry, and the run goes on."""
        try:
            yield
        except Refusal as refusal:
            self.fail(refusal.code, refusal.why, refusal.fix)
        except (OSError, Unanswered, msgspec.DecodeError) as error:
            self.fail(CODE, f"{subject}: {error}", fix)

    def tried[Read](
        self, subject: str, read: Callable[[], Read], otherwise: Read
    ) -> Read:
        """What `read` gives; `otherwise` when it fails, which is a failed step."""
        with self.step(subject, f"the owner checks {subject}"):
            return read()
        return otherwise

    def gone(self, subject: str) -> None:
        """Say what a step removed."""
        self.removed.append(subject)
        click.echo(f"Removed {subject}.", err=True)

    def stays(self, subject: str) -> None:
        """Say what stays on this computer."""
        self.kept.append(subject)
        click.echo(f"Kept {subject}.", err=True)

    def owner(self, line: str) -> None:
        """Say a step that is the owner's to take, once."""
        if line not in self.left_for_owner:
            self.left_for_owner.append(line)
            click.echo(f"For the owner: {line}", err=True)

    def fail(self, code: str, why: str, fix: str) -> None:
        """Say which step failed, and its fix."""
        self.failed.append(Refused(code=code, why=why, fix=fix))
        click.echo(f"Failed: {why}. Fix: {fix}.", err=True)


def ended(report: Report) -> Report:
    """The report, with the `brew` line last; a refusal with the report as its result when a
    step failed, since the app must stay for the run that finishes it."""
    if not report.failed:
        report.owner(BREW)
        return report
    said = Refused(
        code="uninstall-incomplete",
        why="; ".join(one.why for one in report.failed),
        fix="; ".join(
            (*(one.fix for one in report.failed), "then lem uninstall again")
        ),
    )
    encoded = msgspec.Raw(msgspec.json.encode(report))
    output.printed(Envelope(ok=False, outcome=encoded, refusal=said))
    raise click.exceptions.Exit(output.REFUSED)

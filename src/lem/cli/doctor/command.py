"""`lem doctor`: check this machine for the tools Lem needs and recommends.

    lem doctor

Onboarding runs it first, so a repository is never set up for a flow its machine cannot run.
Its result is one row per thing it looked for, `ok`, and after the rows the `brew` lines,
which install each required or recommended program that is absent and that Homebrew ships.
When a required row is not found the check is refused with exit 1, and the envelope keeps the
rows beside the refusal: the owner reads what is missing and how to get it in the same rows as
what is there. A row that is not required never fails it. It answers whatever the versions of
the plugin and the app (`__main__.UNCHECKED`), and only reads: it starts nothing and writes
nothing.
"""

import os

import click
import msgspec

from lem.cli import output, place
from lem.cli.doctor.look import looked
from lem.cli.doctor.row import Report, failing, reported
from lem.cli.doctor.rows import gathered
from lem.kernel.envelope import Envelope, Refused


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem doctor`."""


def refused(report: Report) -> Envelope:
    """The envelope of a check that failed: the rows, and the refusal that names the required
    rows not found."""
    missing = ", ".join(row.name for row in failing(report.rows))
    said = Refused(
        code="doctor",
        why=f"this machine lacks what Lem requires: {missing}",
        fix=(
            "each of those rows in the result says what Lem uses it for and how to get it "
            "(without_it, guide, line), and the result's brew lines install the absent "
            "programs that Homebrew ships; run lem doctor again after"
        ),
    )
    rows = msgspec.Raw(msgspec.json.encode(report))
    return Envelope(ok=False, outcome=rows, refusal=said)


def run(call: Call) -> Report:
    """Every row; a check whose required rows are not all found prints its rows with the
    refusal and exits 1."""
    report = reported(gathered(looked(os.environ, place.folder())))
    if report.ok:
        return report
    output.printed(refused(report))
    raise click.exceptions.Exit(output.REFUSED)


COMMAND = click.Command(
    "doctor",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Check this machine for the tools Lem needs and recommends.",
)

"""`lem prune`: remove what the state folder no longer needs.

    lem prune [--dry-run] [--days N]

Each task that ended with nothing new for `state.keep_days` keeps only its small record, its
journal folded into one summary, and the old folders of the experts, the panels, the naps and
the cast's copies go (`store/retention/`). A dry run removes nothing and says what would go; with
`--days N` it says what would go if the number were N. A removal that failed is a refusal that
names it: the next run finishes it.
"""

import click
import msgspec

from lem.cli import place
from lem.cli.prune import days
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.kernel.errors import Refusal
from lem.store import places
from lem.store.retention import run as retention
from lem.store.retention.said import failed_line, said


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem prune`."""

    dry_run: bool = False
    days: int | None = None


def run(call: Call) -> Envelope:
    """Remove what the state folder no longer needs, or say what would go."""
    where = places.workspace(place.folder())
    keep, source = days.kept(where.checkout, call.days, dry=call.dry_run)
    now = clock.now()
    pruned = retention.pruned(where.state, keep, source, now, dry=call.dry_run)
    if pruned.failed:
        raise refusal(pruned)
    return enveloped(pruned)


def enveloped(pruned: retention.Pruned) -> Envelope:
    """The envelope of a run: what it did, and the owner's line."""
    encoded = msgspec.Raw(msgspec.json.encode(pruned))
    return Envelope(ok=True, outcome=encoded, say=said(pruned))


def refusal(pruned: retention.Pruned) -> Refusal:
    """A run whose removals failed: what it did, and each removal that failed."""
    failed = "; ".join(map(failed_line, pruned.failed))
    return Refusal(
        "prune-failed",
        f"{said(pruned)}, and these removals failed: {failed}",
        "the owner fixes what the errors name; the next lem prune finishes the rest",
    )


COMMAND = click.Command(
    "prune",
    params=[
        click.Option(
            ["--dry-run"], is_flag=True, help="remove nothing: say what would go"
        ),
        click.Option(
            ["--days"],
            type=click.INT,
            help="with --dry-run: what would go if state.keep_days were N",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Remove what the state folder no longer needs.",
)

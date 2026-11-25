"""List the examples or show the ones the caller names."""

import click
import msgspec

from lem.cli.ask import asking, catalog
from lem.cli.ask import spec as specs
from lem.cli.ask.shown import Shown, options


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask demo`."""

    names: tuple[str, ...] = ()


def run(call: Call) -> asking.Words:
    """Open examples in sequence and give the outcome of each page shown."""
    if not call.names:
        return {"outcome": "listed", "demos": catalog.examples()}
    shown = []
    for path in catalog.demos(call.names):
        picked = asking.ask(*specs.load(str(path)), call)
        shown.append(picked)
        if picked.get("outcome") not in ("answered", "dismissed", "chat"):
            break
    last = shown[-1]
    return {**last, "pages": shown}


COMMAND = click.Command(
    "demo",
    params=[
        click.Argument(["names"], nargs=-1),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the demo pages, each by name, or every one.",
)

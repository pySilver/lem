"""Show one question with the options in the command words."""

from pathlib import Path

import click
import msgspec

from lem.cli.ask import asking
from lem.cli.ask.shown import Shown, options
from lem.cli.ask.utf8 import whole


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask q`."""

    prompt: str
    options: tuple[str, ...] = ()
    multi: bool = False
    context: str | None = None
    title: str | None = None


def run(call: Call) -> asking.Words:
    """Make the short form into a question spec."""
    asked: dict[str, object] = {"prompt": whole(call.prompt)}
    if call.options:
        asked["options"] = [
            option(raw, index) for index, raw in enumerate(call.options, 1)
        ]
        asked["width"] = "narrow"
    if call.multi:
        asked["mode"] = "multi"
    if call.context:
        asked["context"] = whole(call.context)
    if call.title:
        asked["title"] = whole(call.title)
    return asking.ask(asked, Path.cwd(), call)


def option(raw: str, index: int) -> dict[str, object]:
    """A label, optional subtitle, and the reason for a recommendation."""
    label, _, rest = whole(raw).lstrip("*").partition("|")
    subtitle, _, why = rest.partition("|")
    marked: dict[str, object] = {"id": f"o{index}", "label": label.strip()}
    if subtitle.strip():
        marked["subtitle"] = subtitle.strip()
    if raw.startswith("*"):
        marked["recommended"] = why.strip() or True
    return marked


COMMAND = click.Command(
    "q",
    params=[
        click.Argument(["prompt"]),
        click.Argument(["options"], nargs=-1),
        *options(),
        click.Option(
            ["--multi"], is_flag=True, help="the owner may pick more than one"
        ),
        click.Option(["--context"], help="what the question is about, above it"),
        click.Option(["--title"], help="the page's title"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask one question with its options, given on the command line.",
)

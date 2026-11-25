"""Render the question spec into an HTML file with its attachments."""

from pathlib import Path

import click
import msgspec

from lem.cli.ask import html, preferences, spec
from lem.kernel import files
from lem.kernel.errors import Refusal


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask render`."""

    spec: str
    out: str


def run(call: Call) -> dict[str, str]:
    """Write the stand-alone page and name it for the owner."""
    asked, base = spec.load(call.spec)
    preferences.apply(asked, preferences.defaults())
    page = html.build(asked, base)
    target = Path(call.out).expanduser().resolve()
    try:
        files.write_whole(target, page)
    except OSError as error:
        raise Refusal(
            "ask-output",
            str(error),
            "give lem ask render a writable --out path",
        ) from error
    return {"outcome": "rendered", "file": str(target)}


COMMAND = click.Command(
    "render",
    params=[
        click.Argument(["spec"]),
        click.Option(["--out", "-o"], required=True, help="the HTML file to write"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Render a spec into an HTML file, attachments kept.",
)

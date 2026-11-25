"""`lem jev ask`: ask the Jev model the questions of a spec, and print its answers.

    lem jev [ask] SPEC

`lem jev SPEC` is this verb; `lem jev check SPEC` reads the spec and asks nothing.
"""

import os
import sys
from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.jev import client, questions

if TYPE_CHECKING:
    from lem.addons.jev.reply import Reply


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem jev ask`."""

    spec: str


def run(call: Call) -> Reply:
    """Ask the spec from a path or standard input."""
    target = client.config(os.environ)
    raw = sys.stdin.buffer.read() if call.spec == "-" else b""
    asked = questions.build(questions.load(call.spec, raw), target.model)
    return client.ask(asked, target, os.environ)


COMMAND = click.Command(
    "ask",
    params=[
        click.Argument(["spec"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Ask the Jev model the questions of a spec, and print its answers.",
)

"""`lem jev check`: read a spec as a request would, and ask nothing.

    lem jev check SPEC

It prints the model, the questions, the address and where the key comes from.
"""

import os
import sys

import click
import msgspec

from lem.addons.jev import client, questions


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem jev check`."""

    spec: str


def run(call: Call) -> client.Check:
    """Check the spec from a path or standard input."""
    target = client.config(os.environ)
    raw = sys.stdin.buffer.read() if call.spec == "-" else b""
    asked = questions.build(questions.load(call.spec, raw), target.model)
    return client.check(asked, target, os.environ)


COMMAND = click.Command(
    "check",
    params=[
        click.Argument(["spec"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Read a spec as a request would, and ask nothing.",
)

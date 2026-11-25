"""`lem session talk`: copy the turns about the task's ask into its talk.md.

    lem session talk SLUG --from WORDS [--leave WORDS]...

It copies the turns of the Claude Code session it runs in, from the owner's turn that the words
of `--from` start, into the task's `talk.md` (`app/sessions/talking.py`).
"""

import os

import click
import msgspec

from lem.adapters import claude_talk, claude_talk_turns
from lem.app.sessions import here, talking
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session talk`."""

    slug: str
    start: str
    leave: tuple[str, ...] = ()


def run(call: Call) -> talking.Copied:
    """Copy the turns about the task's ask into its talk.md."""
    bound = here.bound(place.folder())
    source = claude_talk.own_transcript(os.environ)
    turns = claude_talk_turns.turns(source)
    return talking.copied(bound, call.slug, turns, (call.start, call.leave))


COMMAND = click.Command(
    "talk",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--from", "start"],
            required=True,
            help="the first words of the owner's turn where the topic began",
        ),
        click.Option(
            ["--leave"],
            multiple=True,
            help="the first words of an owner turn of another topic",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Copy the turns about the task's ask into its talk.md.",
)

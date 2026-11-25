"""A run of the night or the retro as `lem proposals add --file` gives it, read from the file
or from standard input and checked before anything is written."""

import sys
from pathlib import Path

import msgspec

from lem.addons.proposals.record import Area
from lem.kernel.errors import Refusal
from lem.records.base import Frozen


class Given(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """One proposal as a run gives it."""

    area: Area
    move: str
    body: str
    source: str
    where: str


class RunGiven(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """A run as `--file` gives it: what it read, and its proposals, none for a run that
    proposes nothing."""

    read: str
    proposals: tuple[Given, ...]


def read_given[Shape](named: str, shape: type[Shape], form: str) -> Shape:
    """The JSON of the file `named`, or of standard input for `-`, as `shape`; refused with
    the form `form` when it does not read."""
    body = bytes_of(named)
    try:
        return msgspec.json.decode(body, type=shape)
    except msgspec.DecodeError as error:
        raise Refusal(
            "form", f"{named} does not read: {error}", f"give {form}"
        ) from error


def bytes_of(named: str) -> bytes:
    """The bytes of the file `named`, or of standard input for `-`."""
    if named == "-":
        return sys.stdin.buffer.read()
    try:
        return Path(named).read_bytes()
    except OSError as error:
        why = f"{named} cannot be read: {error.strerror}"
        raise Refusal("file", why, "name a file that is there") from error


def checked(run: RunGiven) -> RunGiven:
    """The run with its texts stripped; refused for an empty text or a move of two lines."""
    if not run.read.strip():
        raise Refusal(
            "run-read",
            "`read`, what the run read, is empty",
            "say in a line what the run read: the tasks since the last run, the naps, the "
            "night's file",
        )
    for index, given in enumerate(run.proposals, 1):
        if not whole(given):
            raise Refusal(
                "run-proposal",
                f"proposal {index} of the run has an empty move, body, source or where, "
                "or a move of more than one line",
                "give each of the four as text, and the move in one line: its body says "
                "the rest",
            )
    return run


def whole(given: Given) -> bool:
    """Whether every text of `given` is written, its move in one line."""
    texts = (given.move, given.body, given.source, given.where)
    one_line = "\n" not in given.move.strip()
    return one_line and all(text.strip() for text in texts)

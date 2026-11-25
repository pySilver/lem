"""The two keys of the team's settings that the review and its filing read, from the main
checkout's `.lem/settings.toml`: `flow.topics`, what must never go wrong, which the review reads
the diff against, and `jev.findings`, whether a finding's text goes to Jev (true when the file
says nothing, `project.jev_of` on `main`).

A stand-in until the step `settings` gives `Team` its `[flow]` and `[jev]` tables
(`notes/land-review.md`): it reads the two keys alone and refuses a value of another form.
"""

import tomllib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


class Flow(msgspec.Struct, frozen=True, kw_only=True):
    """`[flow]`: the topics, sentences in the owner's words."""

    topics: tuple[str, ...] = ()


class Jev(msgspec.Struct, frozen=True, kw_only=True):
    """`[jev]`: whether a finding's text goes to Jev."""

    findings: bool = True


class Read(msgspec.Struct, frozen=True, kw_only=True):
    """The two tables, each read past its other keys."""

    flow: Flow = Flow()
    jev: Jev = Jev()


def read(checkout: Path) -> Read:
    """The two tables of the main checkout's settings file."""
    path = checkout / ".lem" / "settings.toml"
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Read()
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise Refusal(
            "settings",
            f"{path} does not read: {error}",
            "fix the file, then run the step again",
        ) from error
    try:
        return msgspec.convert(raw, Read)
    except msgspec.ValidationError as error:
        raise Refusal(
            "settings",
            f"{path}: {error}",
            "flow.topics is a list of sentences, jev.findings true or false",
        ) from error

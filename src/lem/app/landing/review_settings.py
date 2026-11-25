"""The two keys of the team's settings that the review and its filing read, from
`.lem/settings.toml` as the base branch has it: `flow.topics`, what must never go wrong, which
the review reads the diff against, and `jev.findings`, whether a finding's text goes to Jev
(true when the file says nothing, `project.jev_of` on `main`).

A stand-in until the step `settings` gives `Team` its `[flow]` and `[jev]` tables and its
loader of the base's file (`notes/land-review.md`): it reads the two keys alone and refuses a
value of another form.
"""

import tomllib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.settings.load import base_of, team_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git

SETTINGS = ".lem/settings.toml"


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


def text_of(git: Git, checkout: Path, base: str | None) -> str | None:
    """The team's settings file as the base branch has it: the main checkout's working tree
    while it is on the base, else the base branch's newest commit, else the working tree
    (`project.load` and `project.committed_settings` on `main`: another branch checked out
    there is no rule for the tasks that run)."""
    path = checkout / SETTINGS
    named = base or base_of(team_of(checkout))
    branch = git.tip(checkout, f"refs/heads/{named}")
    shown = None
    if branch is not None and git.tip(checkout, "HEAD") != branch:
        shown = git.show(checkout, branch, SETTINGS)
    if shown is not None:
        return shown.decode("utf-8", errors="replace")
    return path.read_text(encoding="utf-8") if path.is_file() else None


def read(git: Git, checkout: Path, base: str | None = None) -> Read:
    """The two tables of the team's settings as the base branch has them; `base` is the
    base branch, read from the main checkout's settings when not given."""
    text = text_of(git, checkout, base)
    try:
        raw = tomllib.loads(text or "")
    except tomllib.TOMLDecodeError as error:
        raise Refusal(
            "settings",
            f"{SETTINGS} of {checkout} does not read: {error}",
            "fix the file, then run the step again",
        ) from error
    try:
        return msgspec.convert(raw, Read)
    except msgspec.ValidationError as error:
        raise Refusal(
            "settings",
            f"{SETTINGS}: {error}",
            "flow.topics is a list of sentences, jev.findings true or false",
        ) from error

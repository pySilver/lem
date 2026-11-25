"""What each level of the ladder writes when it settles a decision (`decisions.cmd_log`,
`story` and `steps` on `main`; `stages/ladder.md`).

A count decides each level, not a model, and the lead applies it; this module checks one count
only, two persona votes or more, all for the option taken. A decision past the personas (the
dialectic, the experts) and the lead's pick that no level settled are important, and carry their
story: one concrete case in numbered steps, how the case was had, and its cause.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.decisions import Story

if TYPE_CHECKING:
    from lem.records.decisions import Level

# The fewest votes of the personas that settle a decision, and the fewest steps of a case.
FEWEST_VOTES = 2
FEWEST_STEPS = 2
STEP = re.compile(r"\s*\d+[.)]\s+\S")
PAST_PERSONAS = frozenset(("dialectic", "experts"))
CASE_WAS = ("reproduced", "derived")
CODE = "decision-form"

type Said = tuple[tuple[str, str], ...]


def spaced(text: str) -> str:
    """A text with each run of spaces as one."""
    return " ".join(text.split())


def one_pair(word: str, flag: str, form: str) -> tuple[str, str]:
    """One `NAME=TEXT` of a repeated flag, split at its first `=`."""
    name, sign, said = word.partition("=")
    if not sign or not name.strip() or not said.strip():
        why = f"{flag} {word!r} is not {form}"
        raise Refusal(CODE, why, f"give {flag} {form}")
    return spaced(name), spaced(said)


def said_pairs(words: tuple[str, ...], flag: str, form: str) -> Said:
    """Each `NAME=TEXT` of a repeated flag, each run of spaces as one."""
    return tuple(one_pair(word, flag, form) for word in words)


def by_personas(votes: Said, chose: str) -> Refusal | None:
    """The personas settle a decision with two votes or more, all for the option taken."""
    other = [name for name, option in votes if option != chose]
    voted = len(votes)
    if voted >= FEWEST_VOTES and not other:
        return None
    against = ", ".join(other) or "nobody"
    return Refusal(
        "not-settled",
        f"the personas settle a decision with two votes or more, all for {chose!r}; here "
        f"{voted} voted, and {against} voted otherwise",
        "the ladder goes on to the dialectic (stages/ladder.md)",
    )


def steps(case: str) -> tuple[str, ...]:
    """The case as typed, one step to a line: two numbered steps at the least."""
    lines = case.strip().splitlines()
    rows = tuple(row.rstrip() for row in lines if row.strip())
    numbered = [row for row in rows if STEP.match(row)]
    if len(numbered) >= FEWEST_STEPS:
        return rows
    raise Refusal(
        CODE,
        f"--case has {len(numbered)} numbered steps",
        "--case is one concrete case that ends badly, in numbered steps, one to a line "
        '("1. ...", "2. ..."), with real names and values',
    )


def important(by: Level, *, unsettled: bool) -> bool:
    """Whether a decision carries its story: past the personas, or the lead's unsettled
    pick."""
    return by in PAST_PERSONAS or unsettled


def story_of(case: str | None, case_was: str | None, cause: str | None) -> Story:
    """The story of a decision; a part missing, or a case of how it was not had, is
    refused."""
    told = spaced(cause or "")
    if case is None or case_was is None or not told:
        raise Refusal(
            CODE,
            "an important decision carries its story: --case, --case-was and --cause",
            "--case, one concrete run in numbered steps; --case-was reproduced|derived; "
            "--cause, why it became possible and how far that reaches (prompts/writing.md)",
        )
    if case_was not in CASE_WAS:
        raise Refusal(
            CODE, f"--case-was is {case_was!r}", "--case-was reproduced|derived"
        )
    was = "reproduced" if case_was == "reproduced" else "derived"
    return Story(case=steps(case), case_was=was, cause=told)

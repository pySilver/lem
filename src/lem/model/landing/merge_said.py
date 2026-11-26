"""What the merge agent's reply says, and the lines Lem writes of a reply it cannot record
(`landing.md` E, "Two unusable answers"; `main:land.verdict_of`, `base_call_of`, `unread_why`).

The verdict is the first line that is not empty, past a heading's, a quote's or a bold mark:
`Verdict: merge` or `Verdict: call`, the label required, as `main:land.VERDICT` reads it. On a
base that moved after the checks, the second such line is `Base: safe` or `Base: another round`,
the label required, then one sentence of why. A line without its label is no verdict, so prose
("Merge conflicts remain.") never reads as one.
"""

import re
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

if TYPE_CHECKING:
    from lem.records.landing.propose import MergeRead

type Verdict = Literal["merge", "call"]
type BaseCall = Literal["safe", "another round"]
VERDICT = re.compile(r"Verdict:\s*(merge|call)\b", re.IGNORECASE)
BASE_CALL = re.compile(
    r"Base:\s*(safe|another round)\b[.:;,]?\**\s*(.*)", re.IGNORECASE
)
# The marks a line may open with: a heading's, a quote's, a bold mark (`main:land.line_verdict`).
OPENING = "#*> \t"
# What may stand between the verdict and its sentence of why.
TRIM = " .:;,*-"
# The start of the why of another round that Lem recorded because the merge agent's answer
# could not be recorded twice on a moved base: Lem's words, never the agent's.
UNRECORDED = "the merge agent's answer could not be recorded twice"
ROUND: BaseCall = "another round"
# The answers that cannot be recorded for one tip and base: the second settles the read
# (`main:land.MERGER_TRIES`).
TRIES = 2


def lines_of(reply: str) -> list[str]:
    """The reply's lines that are not empty, each past its opening marks."""
    found = (line.lstrip(OPENING).rstrip() for line in reply.splitlines())
    return [line for line in found if line]


def verdict_of(reply: str) -> Verdict | None:
    """The verdict on the reply's first line that is not empty, or None."""
    lines = lines_of(reply)
    found = VERDICT.match(lines[0]) if lines else None
    if found is None:
        return None
    word = found.group(1).lower()
    return "merge" if word == "merge" else "call"


def base_call_of(reply: str) -> tuple[BaseCall, str] | None:
    """The call on a moved base on the reply's second line that is not empty, with its
    sentence of why; None for no call, or a call with no why."""
    # The two fallback strings both fail the base-call pattern.
    second = next(iter(lines_of(reply)[1:]), "")  # pragma: no mutate
    found = BASE_CALL.match(second)
    if found is None:
        return None
    why = found.group(2).strip().strip("*").strip()
    if not why:
        return None
    call: BaseCall = "safe" if found.group(1).lower() == "safe" else "another round"
    return call, why


def problem_of(reply: str | None, *, moved: bool) -> str | None:
    """What keeps the reply from being recorded as it is, in a few words, or None: no
    answer, no verdict on its first line, or no call on a moved base."""
    if reply is None:
        return "it ended with no answer"
    if verdict_of(reply) is None:
        return "its first line gave no verdict"
    if moved and base_call_of(reply) is None:
        return "its second line gave no call on the moved base"
    return None


def unread_why(reply: str | None) -> str:
    """Why a second answer that cannot be recorded, on a base that did not move, calls the
    owner: what the last answer holds, never a verdict of a lower line as the verdict."""
    if reply is None:
        return (
            "the merge agent twice gave no answer with a verdict on its first line; "
            "its last try ended with no answer"
        )
    lower = next(
        (
            found.group(1).lower()
            for found in map(VERDICT.match, lines_of(reply)[1:])
            if found
        ),
        None,
    )
    last = (
        f"its last answer puts another line above its verdict, `Verdict: {lower}.`"
        if lower
        else "its last answer gives no verdict at all"
    )
    return f"the merge agent twice gave no verdict on its first line; {last}"


def answered(read: MergeRead, reply: str, *, moved: bool) -> MergeRead:
    """`read` with the reply's verdict and its sentence of why: on a moved base the call on
    the move and that call's sentence; else what follows the verdict on its line, or the
    next line. The verdict's own word is never the why."""
    verdict = verdict_of(reply)
    call = base_call_of(reply) if moved else None
    if call is not None:
        return replace(read, verdict=verdict, base_call=call[0], why=call[1])
    lines = lines_of(reply)
    rest = VERDICT.sub("", lines[0], count=1).lstrip(TRIM)
    why = rest or next(iter(lines[1:]), None)
    return replace(read, verdict=verdict, why=why)


def unrecorded(
    read: MergeRead, said: tuple[str | None, str], *, count: int, moved: bool
) -> MergeRead:
    """`read` for an answer that could not be recorded (`said`: the reply, or None, and what
    is wrong with it), the `count`-th for its tip and base. The first keeps what is wrong; the
    second settles: on a `moved` base it is another round, and on a base that did not move a
    call of the owner with no verdict."""
    reply, problem = said
    if count < TRIES:
        # The count starts at one and only the first reply takes this path.
        return replace(read, attempts=count, why=problem)  # pragma: no mutate
    if moved:
        why = f"{UNRECORDED} ({problem}), and in doubt the checks run again"
        return replace(read, attempts=count, base_call=ROUND, why=why)
    return replace(read, attempts=count, why=unread_why(reply))

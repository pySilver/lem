"""What `read --record` refuses in a review's record that its decoder takes: an attempt that
is not the one due, a tip that is not the branch's, no careful call, a careful change under the
full set, a round with no profile named, a full set that leaves one out, findings nobody
answered for, and a lowered bar the record says nothing of (`land.cmd_read` on `main`).

A record that no source answered (`answered` empty, each source in `silent` with why, nothing
found) is a silent attempt: it makes no careful call and counts as an attempt.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.review_said import Said, defects

if TYPE_CHECKING:
    from lem.model.landing.review_due import Floor

SHA = re.compile(r"[0-9a-f]{40}")
# The characters of a commit wherever a refusal of `read` names one in short.
SHORT = 12
KIND_SAYS = (
    ("read", "one read"),
    ("round", "a review round with the profiles that fit"),
    ("full", "the project's full set"),
)


def silent(said: Said) -> bool:
    """Whether the record is of an attempt that no source answered: nobody in `answered`,
    each source in `silent`, and nothing found."""
    found = said.must_fix or said.should or said.nit or defects(said)
    return not said.answered and bool(said.silent) and not found


def tip_refused(said: str, tip: str, slug: str) -> Refusal | None:
    """Why a record whose `tip` is `said` is not the review of the branch at `tip`."""
    if said == tip:
        return None
    if not SHA.fullmatch(said):
        why = (
            "`tip` in the record is the whole commit the review read, 40 hex digits, as "
            f"`lem land read {slug}` printed it, and it is {said!r}"
        )
        return Refusal("tip", why, f"write the tip lem land read {slug} printed")
    was, now = said[:SHORT], tip[:SHORT]
    return Refusal(
        "tip",
        f"the record is of the review of {was}, and the branch is at {now} now: that "
        "review read another change, and it is not written down",
        f"lem land read {slug} says what is due for this one",
    )


def attempt_refused(
    said: Said, attempt: int, recorded: tuple[int, ...]
) -> Refusal | None:
    """Why the record is not of the attempt that is due; a record sent again is written down
    already."""
    if said.attempt == attempt:
        return None
    ending = (
        "that review is written down already"
        if said.attempt in recorded
        else "`lem land read` prints the number a record carries"
    )
    return Refusal(
        "attempt",
        f"the record says attempt {said.attempt}, and the next review of this task is "
        f"attempt {attempt}: {ending}",
        "the review writes the attempt that lem land read printed",
    )


def under_floor(said: Said, least: Floor, slug: str) -> Refusal | None:
    """Why the review is less than the change gets at the least."""
    kinds = dict(KIND_SAYS)
    order = tuple(kinds)
    if order.index(said.kind) >= order.index(least.kind):
        return None
    gets, given = kinds[least.kind], kinds[said.kind]
    return Refusal(
        "under-floor",
        f"this change gets {gets} at the least ({least.why}), and the record says {given}",
        f"run {gets}, then lem land read {slug} --record FILE",
    )


def call_refused(said: Said, slug: str) -> Refusal | None:
    """Why the careful call is missing, or a careful change was not given the full set. A
    silent attempt makes no call."""
    if said.careful is None or said.careful_why is None:
        if silent(said) and said.careful is None and said.careful_why is None:
            return None
        return Refusal(
            "no-careful-call",
            'the record makes the careful call: "careful": true or false, the review\'s '
            "own reading of the diff against each of the project's topics, and "
            '"careful_why": one line that names the topic the change reaches, or what was '
            "checked to say that it reaches none",
            f"the review writes careful and careful_why in its record of {slug}",
        )
    if said.careful and said.kind != "full":
        given = dict(KIND_SAYS)[said.kind]
        return Refusal(
            "careful-not-full",
            "a change the review calls careful gets the project's full set, and the record "
            f"says {given}",
            'the review runs the full set and writes its record with "kind": "full"',
        )
    return None


def names_refused(said: Said) -> Refusal | None:
    """Why the record does not name what it ran, leaves out, or who found its findings."""
    if said.kind != "read" and not said.ran and not silent(said):
        return Refusal(
            "ran",
            "a round names each profile it ran in `ran`, with why that profile fits this "
            "change",
            'write "ran": [{"name": PROFILE, "why": WHY}, ...] in the record',
        )
    if said.kind == "full" and said.left_out:
        return Refusal(
            "left-out",
            "the project's full set leaves no profile out: a profile may be added to it, "
            "never dropped",
            'write "left_out": [] on a full review',
        )
    found = said.must_fix or said.should or said.nit or defects(said)
    if found and not said.answered:
        return Refusal(
            "answered",
            "the record has findings and no source that answered",
            "`answered` names who found them",
        )
    return None


def bar_refused(said: Said, lowered: tuple[str, ...]) -> Refusal | None:
    """Why the record says nothing of a file in which the change lowers the bar: the owner
    reads each such file himself, with the review's word on the builder's reason."""
    told = {named.name for named in said.lowered}
    unsaid = [path for path in lowered if path not in told]
    if not said.answered or not unsaid:
        return None
    listed = ", ".join(unsaid)
    return Refusal(
        "bar",
        f"the change lowers the bar in {listed} and the record says nothing of it",
        '`bar` holds one {"name": FILE, "why": WHAT THE REVIEW SAYS OF THE BUILDER\'S '
        "REASON} for each such file",
    )

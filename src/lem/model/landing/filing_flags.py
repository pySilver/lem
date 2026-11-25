"""The words of `lem land file` that judge an item the defect may be: `--same rN.M=PATH`, the
item of the tip that holds the defect, and `--new rN.M`, a defect of its own; and `--again`,
which writes once more each item `file` filed that is gone from the tip (`land.same_flags` and
`land.cmd_file` on `main`). Each wrong word is refused before Jev is asked or a file written.
"""

import re

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

NUMBER = re.compile(r"r\d+\.\d+")
JOINED = ", "


class Flags(Frozen, frozen=True, kw_only=True):
    """The words of one run of `file`."""

    again: bool = False
    same: tuple[str, ...] = ()
    new: tuple[str, ...] = ()


def same_of(
    flags: Flags, folder: str, paths: frozenset[str]
) -> Refusal | dict[str, str]:
    """Each defect `--same` names with its item, a file of the backlog folder at the tip; a
    word of another form is refused."""
    found: dict[str, str] = {}
    for flag in flags.same:
        number, _, path = (part.strip() for part in flag.partition("="))
        if not NUMBER.fullmatch(number) or path not in paths:
            return Refusal(
                "same",
                f"--same {flag!r} is no defect and item: it is `--same rN.M=PATH`, the number "
                f"of a defect (`r1.2`) and the path of the item of the backlog folder {folder} "
                "that holds it, a file of the task's tip",
                "name the defect and the item as lem land file named them",
            )
        found[number] = path
    return found


def both_refused(same: dict[str, str], flags: Flags) -> Refusal | None:
    """Why a defect is named by both `--same` and `--new`."""
    both = sorted(set(same) & set(flags.new))
    if not both:
        return None
    listed = JOINED.join(both)
    return Refusal(
        "same-new",
        f"{listed} is named by both --same and --new",
        "a defect is the item it names (--same), or a defect of its own (--new)",
    )


def stray_refused(named: set[str], free: set[str]) -> Refusal | None:
    """Why `--same` or `--new` names a defect that waits for no item, or has an open item of
    its own."""
    stray = sorted(named - free)
    if not stray:
        return None
    listed = JOINED.join(stray)
    ending = ", and none waits here"
    if free:
        ones = JOINED.join(sorted(free))
        ending = f", and the ones here are {ones}"
    return Refusal(
        "same-new",
        f"{listed} is no defect that waits for an item with no open item of its own{ending}",
        "--same and --new name such a defect by its number",
    )


def gone_refused(gone: tuple[str, ...], slug: str, *, again: bool) -> Refusal | None:
    """Why `file` stops at an item it filed that the tip no longer holds, unless `--again`
    writes it once more."""
    if again or not gone:
        return None
    listed = JOINED.join(gone)
    return Refusal(
        "item-gone",
        f"{listed}, filed for a review of {slug}, is gone from the tip",
        f"lem land file {slug} --again writes it once more; or a builder commits it back",
    )

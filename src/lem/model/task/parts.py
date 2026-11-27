"""The parts of a feature, from the headings of its criteria (`lem task split`;
`docs/plans/2026-11-27-a-feature-in-parts.md`, "The order of the parts").

Each heading but `### The whole feature` is one part, `SLUG: WORDS`: the part's slug, then its
ask, the words of the owner's page. A heading that ends in `(independent)` waits for nothing;
every other part waits for the part before it, in the order of the headings. A split has one
part at the least, and the group of the whole feature has a criterion too: its criteria are
the feature's own, which its end proves.
"""

import re

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.records.criterion import Criterion
from lem.store.places import SLUG

CODE = "split"
HEADING = re.compile(
    rf"^(?P<slug>{SLUG.pattern}):\s+(?P<ask>\S.*?)(?P<independent>\s+(?i:\(independent\)))?$"
)
FORM = (
    "each part's heading is ### SLUG: WHAT IT DOES, with (independent) at its end for a "
    "part that waits for none before it, and ### The whole feature holds what only the "
    "whole feature meets"
)


class Part(Frozen, frozen=True, kw_only=True):
    """One part: its slug and ask from its heading, the heading as the criteria keep it,
    whether it is marked independent, the part it waits for (none for the first and for one
    marked independent), and its criteria as the feature's criteria hold them."""

    slug: str
    ask: str
    heading: str
    independent: bool = False
    after: tuple[str, ...] = ()
    criteria: tuple[Criterion, ...] = ()


def headed(heading: str, feature: str) -> Part:
    """The part a heading names, with no criteria yet; a heading of another form, and a part
    that takes the feature's own slug, are refused."""
    found = HEADING.match(heading)
    if found is None:
        raise Refusal(CODE, f"the heading {heading!r} names no part", FORM)
    slug = found["slug"]
    if slug == feature:
        raise Refusal(
            CODE,
            f"the heading {heading!r} names the feature {feature} itself",
            "a part takes a slug of its own",
        )
    independent = found["independent"] is not None
    return Part(slug=slug, ask=found["ask"], heading=heading, independent=independent)


def grouped(criteria: tuple[Criterion, ...]) -> dict[str, list[Criterion]]:
    """The criteria of each part, by its heading, in the order of the headings."""
    groups: dict[str, list[Criterion]] = {}
    for criterion in criteria:
        if criterion.part is not None:
            groups.setdefault(criterion.part, []).append(criterion)
    return groups


def ordered(parts: list[Part]) -> tuple[Part, ...]:
    """The parts, each waiting for the one before it unless it waits for none."""
    befores = [None, *(before.slug for before in parts[:-1])]
    return tuple(
        part if part.independent or before is None else replace(part, after=(before,))
        for part, before in zip(parts, befores, strict=True)
    )


def twice(parts: list[Part]) -> None:
    """Refuse two headings of one slug."""
    seen: set[str] = set()
    for part in parts:
        if part.slug in seen:
            raise Refusal(
                CODE,
                f"two headings name the part {part.slug}",
                "a part takes one heading",
            )
        seen.add(part.slug)


def parts_of(feature: str, criteria: tuple[Criterion, ...]) -> tuple[Part, ...]:
    """The parts of the feature's criteria, in the order of their headings; criteria with no
    part's heading, two parts of one slug, and no criterion of the whole feature are
    refused."""
    groups = grouped(criteria)
    if not groups:
        raise Refusal(CODE, f"the criteria of {feature} have no part's heading", FORM)
    if all(criterion.part is not None for criterion in criteria):
        raise Refusal(
            CODE,
            f"the criteria of {feature} have no criterion under ### The whole feature",
            "the whole feature has a criterion of its own, which its end proves",
        )
    parts = [
        replace(headed(heading, feature), criteria=tuple(found))
        for heading, found in groups.items()
    ]
    twice(parts)
    return ordered(parts)

"""A decision's story (`board_task.story`, `options_rows`, `option_parts` and `picks_of` on
`main`): the case as numbered steps and how it is known, why it could happen, this or that with
the option taken and the experts that picked it, and who took it. A record with no story gives
what it has, and one with none of it has no story."""

import re
from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Case
from lem.board.inputs.task.decisions import Option, Story
from lem.board.views.criteria.says import chosen_at
from lem.board.views.criteria.terms import CASE_WAS, EXPERTS
from lem.board.views.words import capital

if TYPE_CHECKING:
    from lem.records.decisions import Taken

QUOTES = ('"', "“", "”")
SINGLE_OPEN = re.compile(r"(?:^|\s)['\u2018]")
SINGLE_CLOSE = re.compile(r"\w['\u2019](?=\s|$|[.,;])")


def parts_of(option: str) -> tuple[str, str]:
    """An option's label and what it leads to (`LABEL: what it leads to`), cut at its first
    colon outside a quote; no label when it has none."""
    head, colon, rest = option.partition(":")
    label, leads = head.strip(), rest.strip()
    if not colon or quoted(head) or not label or not leads:
        return "", option
    return label, leads


def quoted(head: str) -> bool:
    """Whether a quote opens before the colon and does not close: the colon is in it."""
    marks = sum(head.count(mark) for mark in QUOTES)
    opened = len(SINGLE_OPEN.findall(head))
    closed = len(SINGLE_CLOSE.findall(head))
    return marks % 2 == 1 or opened > closed


def options_of(taken: Taken) -> tuple[Option, ...]:
    """This or that: each option, the one taken marked, with the experts who picked it."""
    at = chosen_at(taken)
    return tuple(
        option_of(taken, option, taken=index == at)
        for index, option in enumerate(taken.options)
    )


def option_of(decision: Taken, option: str, *, taken: bool) -> Option:
    """One option, and the experts who picked it: each one that answered picked the option
    the experts took."""
    label, leads = parts_of(option)
    advisers = decision.advisers or tuple(EXPERTS)
    names = tuple(EXPERTS.get(key, key) for key in advisers)
    picks = decision.by == "experts" and option == decision.chose
    return Option(
        label=label, leads=leads or None, taken=taken, picked=names if picks else ()
    )


def story_of(taken: Taken, how: str) -> Story | None:
    """The decision's story, or None when its record tells none."""
    story = taken.story
    options = options_of(taken)
    if story is None and not options:
        return None
    none_taken = taken.chose if options and chosen_at(taken) < 0 else None
    return Story(
        case_was=CASE_WAS[story.case_was] if story else None,
        cases=(Case(steps=story.case),) if story and story.case else (),
        cause=story.cause if story else None,
        options=options,
        none_taken=none_taken,
        who=capital(how),
    )

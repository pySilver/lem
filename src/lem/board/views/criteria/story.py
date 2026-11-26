"""A decision's story (`board_task.story`, `options_rows`, `option_parts` and `picks_of` on
`main`): the case as numbered steps and how it is known, why it could happen, this or that with
the option taken and the experts that picked it, and who took it. A record with no story gives
what it has, and one with none of it has no story."""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.inputs.task.criteria import Case
from lem.board.inputs.task.decisions import Option, Story
from lem.board.views.criteria.says import chosen_at
from lem.board.views.criteria.terms import CASE_WAS, EXPERTS
from lem.board.views.words import capital

if TYPE_CHECKING:
    from lem.records.decisions import Taken

MARKS = re.compile("[:'\"\u201c\u201d\u2018\u2019]")
APOSTROPHE = "'"
CLOSERS = MappingProxyType(
    {
        '"': '"',
        APOSTROPHE: APOSTROPHE,
        "\u201c": "\u201d",
        "\u2018": "\u2019",
    }
)


def parts_of(option: str) -> tuple[str, str]:
    """An option's label and what it leads to, cut at its first colon outside a quote."""
    cut = delimiter(option)
    if cut is None:
        return "", option
    label = option[:cut].strip()
    leads = option[cut + 1 :].strip()
    return (label, leads) if label and leads else ("", option)


def delimiter(option: str) -> int | None:
    """The first colon outside a quotation."""
    closing = None
    for mark in MARKS.finditer(option):
        at = mark.start()
        if closing is None and mark[0] == ":":
            return at
        closing = next_quote(option, at, closing)
    return None


def next_quote(option: str, at: int, closing: str | None) -> str | None:
    """The quote that is open after this mark, if any."""
    char = option[at]
    if closing is None:
        before = option[at - 1 : at]
        return None if char == APOSTROPHE and before.isalnum() else CLOSERS.get(char)
    after = option[at + 1 : at + 2]
    in_word = char in (APOSTROPHE, "\u2019") and after.isalnum()
    return None if char == closing and not in_word else closing


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

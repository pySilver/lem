"""A line a stage wrote of a task, as the board says it (`board_model.words` and `yours` on
`main`): a fixed line of Lem's in words the owner reads, the third person of the stages turned to
him, and every address of a pull request a link with its number.

Any other line is the agent's own and stays as written.
"""

import re
from types import MappingProxyType

from lem.board.inputs.names import title_of
from lem.model.criteria import waits

# The fixed lines, each with what the board says in its place.
FIXED = MappingProxyType(
    {
        "small change: one builder": "one builder makes the change",
        "lead: session": "its companion talks the plan through",
        waits.CHANGED: "the criteria changed from your note, and wait for your yes again",
        waits.UNCHANGED: (
            "your note changed no criterion, and the criteria wait for your yes again"
        ),
    }
)
BUILDER = "lead: builder"
BREAKER = re.compile(r"breaker [1-9]\d* waits for the owner\b.*")
PLAN = re.compile(r"plan committed\b(?:\D*(?P<count>\d+) tasks?)?.*")
AFTER = re.compile(r"(?:it starts )?after:? (?P<slug>[a-z0-9-]+)")
OWNERS = re.compile(r"\b(waits?|waiting) for the owner['’]s\b")
OWNER = re.compile(r"\b(waits?|waiting) for the owner\b")
PULL = re.compile(r"\bhttps?://\S+/pull/(\d+)\b")


def said(line: str, *, talked: bool = False) -> str:
    """A stage's line as the page says it; `talked` when a plan talk ended before it."""
    text = " ".join(line.split())
    fixed = FIXED.get(text)
    if fixed is not None:
        return fixed
    if text.startswith(BUILDER):
        if talked:
            return "an agent builds the plan its companion talked through"
        return "an agent plans and builds it"
    return linked(yours(patterned(text)))


def patterned(text: str) -> str:
    """A line of a fixed pattern in words: a breaker that waits, a plan committed, a task it
    starts after; any other as it is."""
    if BREAKER.fullmatch(text):
        return "the build stopped, and its breaker waits for you"
    plan = PLAN.fullmatch(text)
    if plan and plan["count"]:
        count = int(plan["count"])
        tasks = "task" if count == 1 else "tasks"
        return f"the plan is committed, with {count} {tasks}"
    if plan:
        return "the plan is committed"
    after = AFTER.fullmatch(text)
    if after:
        return f"it starts after “{title_of(after['slug'])}” ends"
    return text


def yours(text: str) -> str:
    """The stages write what waits for the owner in the third person; the page speaks to
    him."""
    theirs = OWNERS.sub(r"\1 for your", text)
    return OWNER.sub(r"\1 for you", theirs)


def linked(text: str) -> str:
    """Each address of a pull request in `text` as a markdown link with its number."""
    return PULL.sub(link_of, text)


def link_of(found: re.Match[str]) -> str:
    """The markdown link of one address of a pull request."""
    number, url = found[1], found[0]
    return f"[#{number}]({url})"


def capital(text: str) -> str:
    """The text with its first letter in capitals."""
    return text[:1].upper() + text[1:]

"""The words of each row of a skill an agent loads by name: what Lem uses it for, what happens
without it, its need and the guide to install it by.

The recipes of the agterm cookbook that Lem needs (webrev, the backlog) are required, and each
has the guide the developer installs it by. agdoc is recommended: no step of Lem makes its page
since the merge agent's `merge-review.md` took the place of the owner's page of a task (the
owner's ruling of 2026-11-20).
"""

import msgspec

from lem.cli.doctor.row import RECOMMENDED, REQUIRED, Need
from lem.cli.doctor.tool_words import COOKBOOK


class Skill(msgspec.Struct, frozen=True, kw_only=True):
    """A skill, and the words of its row."""

    name: str
    used_for: str
    without_it: str
    need: Need = REQUIRED
    guide: str | None = None


REVMUX = Skill(
    name="revmux",
    used_for=(
        "how an agent runs a review round: it writes the round's context and reads the "
        "findings back"
    ),
    without_it=(
        "an agent has the review tool and no instructions for it; install the skill that "
        "comes with revmux (its README says how)"
    ),
)
WEBREV = Skill(
    name="webrev",
    used_for=(
        "the owner marks up a plan, a draft or any document as a rendered page, and the "
        "notes come back to the agent"
    ),
    without_it=(
        "Lem cannot open a plan or a document for the owner to mark up; install the recipe "
        "from its guide"
    ),
    guide=f"{COOKBOOK}annotate-document",
)
AGDOC = Skill(
    name="agdoc",
    used_for=(
        "a page about an issue, a plan or a change that the owner asks for himself, to "
        "read in agterm"
    ),
    without_it="no step of Lem needs it; the owner has no page of his own to ask for",
    need=RECOMMENDED,
    guide=f"{COOKBOOK}html-doc-overlay",
)
BACKLOG = Skill(
    name="backlog",
    used_for=(
        "the owner's own view of the backlog items in docs/backlog/, and the picker that "
        "adds and opens them"
    ),
    without_it=(
        "the owner has no tool of his own for the backlog; install the recipe from its "
        "guide, for the user (~/.claude/skills/backlog) or for this repository "
        "(.claude/skills/backlog)"
    ),
    guide=f"{COOKBOOK}backlog-picker",
)
MAILBOX = Skill(
    name="mailbox-chat",
    used_for="how an agent sends to the other pane and reads what comes back",
    without_it=(
        "an agent has the command and no instructions for it; the same recipe of agterm's "
        "cookbook installs the skill"
    ),
)

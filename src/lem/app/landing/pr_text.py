"""The pull request's text, in the order the owner reads it (`main:land.pr_text`,
`small_text`): green or each reason it is not, then the request in the owner's words, the
criteria with their tests, each check with what it returned, each decision of the record with
who took it and why, and the agent's notes with what was seen outside the change.

The text is a function of the record, the facts of the branch and the notes, so a proposal cut
off and made again writes the same bytes. Each body is published at a path of its own,
`pr-ROUND-DIGEST.md`, which the record cites. The template only prints its blocks.
"""

from typing import TYPE_CHECKING

import jinja2

from lem.app.landing import pr_criteria, pr_fast, pr_head, pr_standard
from lem.app.landing.pr_inputs import Text
from lem.kernel import files
from lem.model.landing.propose_facts import small

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.propose import Proposal
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

SHORT = 12
TEMPLATES = jinja2.Environment(
    loader=jinja2.PackageLoader("lem.app.landing", "templates"),
    autoescape=jinja2.select_autoescape(default=False, default_for_string=False),
    undefined=jinja2.StrictUndefined,
    keep_trailing_newline=True,
)


def body(record: Record, proposal: Proposal, facts: Facts) -> str:
    """The whole text of the pull request."""
    track = pr_fast.blocks if small(record) else pr_standard.blocks
    head = (*pr_head.blocks(record, proposal), *pr_criteria.request(record))
    blocks = (*head, *track(record, proposal, facts))
    return TEMPLATES.get_template("pr.md.j2").render(text=Text(blocks=blocks))


def published(folder: Path, number: int, text: str) -> str:
    """Publish the text in the task's folder `folder` at a path named by the round and its
    digest, and give that path."""
    encoded = text.encode()
    short = files.digest(encoded)[:SHORT]
    named = f"pr-{number}-{short}.md"
    files.publish(folder / named, encoded)
    return named

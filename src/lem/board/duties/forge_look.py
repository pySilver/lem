"""The board server's look at the forge for one workspace (`serve.forge_once` on `main`): each
open task's pull request as the forge reports it, at most every SECONDS, written whole into
`forge.json`, which the board's conflict mark, the list of what waits and the conflict's wake
read (`app/owner/forge.py` holds its form).

A workspace with no pull request open asks nothing, and nor does one whose origin is not on
GitHub. A look the forge does not answer is the board's problem, in the forge's own words.
"""

import re
from datetime import timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING

import msgspec

from lem.app.init.origin import GITHUB
from lem.app.owner import forge
from lem.kernel import files
from lem.kernel.errors import Fault, Refusal
from lem.store import guard

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.ports.forge_facts import Pull

# How often, at most, the server asks the forge about one workspace's open pull requests. A
# guess (2026-11-20): a merge on GitHub shows within a few minutes, and a call a few minutes
# stays far under the forge's limits.
LOOK_SECONDS = 180
SECONDS = timedelta(seconds=LOOK_SECONDS)
PROBLEM = "forge"
# The forge's `mergeable` in GitHub's own words, as `forge.json` keeps it.
CALLED = MappingProxyType(
    {"conflicting": forge.CONFLICTING, "mergeable": "MERGEABLE", "unknown": "UNKNOWN"}
)
SIGNED_OUT = re.compile("auth|login", re.IGNORECASE)

type Pulls = dict[str, Pull]


def due(duty: Duty) -> bool:
    """Whether the look is due: the first one, or SECONDS after the last, at a GitHub origin."""
    looked = duty.kept.looked
    if looked is not None and duty.now - looked < SECONDS:
        return False
    url = duty.here.ports.git.origin_url(duty.checkout)
    return bool(url and GITHUB.match(url))


def looked(duty: Duty, numbers: dict[str, int]) -> Pulls | None:
    """Each task's pull request as the forge reports it now; None, with the board's problem,
    when the forge does not answer."""
    duty.kept.looked = duty.now
    try:
        pulls = {
            slug: duty.here.ports.forge.pull(number) for slug, number in numbers.items()
        }
    except (Fault, Refusal) as error:
        problem = problem_of(error)
        duty.kept.problems[PROBLEM] = problem
        duty.say(problem)
        return None
    duty.kept.problems.pop(PROBLEM, None)
    return pulls


def problem_of(error: Fault | Refusal) -> str:
    """The board's line for a look the forge did not answer."""
    why = str(error)
    if isinstance(error, Refusal):
        why = f"{error.why}. {error.fix}"
    elif SIGNED_OUT.search(why):
        why = "`gh` is not signed in to github.com (`gh auth login` signs it in)"
    return f"the board cannot ask GitHub about the open pull requests: {why}"


def written(duty: Duty, pulls: Pulls) -> None:
    """Write the look into `forge.json`, whole; a write that fails is a line in the server's
    log, and the look holds in memory meanwhile."""
    seen = {
        slug: forge.Seen(head=pull.head, mergeable=CALLED[pull.mergeable])
        for slug, pull in pulls.items()
    }
    look = forge.Look(looked=duty.now, seen=seen)
    guard.writable(duty.state)
    try:
        files.write_whole(duty.state / forge.LOOK, msgspec.json.encode(look))
    except OSError as error:
        duty.say(f"the forge's look was not written to {forge.LOOK}: {error}")

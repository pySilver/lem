"""`lem issue land SLUG`: the task landed. One comment with what changed, the pull request and
green or not; then the issue is closed as completed, unless it is closed already. Each run
skips what is written down, so a landing that still owes the issue a step pays only that."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks.issues import guard, words
from lem.app.tasks.issues.comment import commented

if TYPE_CHECKING:
    from lem.app.tasks.issues.results import Stepped
    from lem.app.wiring import Ports
    from lem.store.places import Workspace

STEP = "land"


def land(ports: Ports, where: Workspace, slug: str) -> Stepped:
    """The landing's comment and close on the task's issue."""
    run = guard.run_of(ports, where, slug, STEP)
    commented(run, STEP, words.landed(run.state, run.record))
    if "landed" in run.acts:
        return run.stepped(STEP, None)
    issue = run.issues.issue(run.repo, run.number)
    if issue.state != "closed":
        run.issues.close(run.repo, run.number)
        run.did.append("closed the issue as completed")
        issue = replace(issue, state="closed")
    run.write("landed")
    return run.stepped(STEP, issue)

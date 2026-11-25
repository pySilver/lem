"""Records and worlds for the cases of `model/landing`: a fast-track task at each point of its
plain landing, and the world that holds for it, each changed by the fields a case names."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.model.criteria import contract
from lem.model.landing import checks
from lem.model.landing.world import PullSeen, Rules, World
from lem.records.approvals import Approval
from lem.records.criteria import Criteria
from lem.records.criterion import Criterion
from lem.records.landing.checks import Checked
from lem.records.landing.merge import Merged
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.landing.review import Filed, Finding, Reviewed
from lem.records.landing.start import Based, Started
from lem.records.task import Shape

if TYPE_CHECKING:
    from lem.records.record import Record

TIP = "1" * 40
BASE = "b" * 40
TREE = "e" * 40
OTHER = "9" * 40
MERGE = "c" * 40
BRANCH = "docs/fix-the-login"
RULES = Rules(base="main", commands=("true",))
CRITERION = Criterion(number=1, text="The login works.", no_test="it keeps behavior")
APPROVED = Approval(
    number=1,
    at=MOMENT,
    by="lem",
    size="small",
    why="one word",
    digest="d",
    criteria=(CRITERION,),
)
NIT = Finding(
    id="r1.1",
    level="nit",
    where="a.py",
    title="a nit",
    what="it",
    against="under",
    why="small",
)


def world(**fields: object) -> World:
    """The world of a clean worktree whose tip holds origin's base, with `fields` over it."""
    made = World(
        rules=RULES,
        branch=BRANCH,
        base=BASE,
        base_tree=TREE,
        now=MOMENT,
        tip=TIP,
        tree=TREE,
        clean=True,
        base_in_tip=True,
        local=TIP,
    )
    return replace(made, **fields)


def task(status: str = "landing", **landing: object) -> Record:
    """A fast-track task in `status`, its criterion approved, with the landing's `landing`."""
    criteria = Criteria(
        size="small", why="one word", criteria=(CRITERION,), approvals=(APPROVED,)
    )
    shape = Shape(type="docs", why="a word", track="small")
    made = record(status=status, shape=shape, branch=BRANCH, criteria=criteria)
    if not landing:
        return made
    return replace(made, landing=replace(Landing(), **landing))


STARTED = Started(round=1, branch=BRANCH, base_ref="main", at=MOMENT)
BASED = Based(tip=TIP, base=BASE, before=TIP, carried=False, at=MOMENT)
CHECKED = Checked(
    tip=TIP,
    tree=TREE,
    base=BASE,
    inputs=checks.inputs(RULES),
    outcome="passed",
    at=MOMENT,
)
REVIEWED = Reviewed(
    attempt=1,
    tip=TIP,
    of="change",
    scope="whole",
    floor="read",
    kind="read",
    careful=False,
    answered=("claude",),
    findings=(NIT,),
    to_file=("r1.1",),
    at=MOMENT,
)
FILED = Filed(finding="r1.1", disposition="seen", line="under: small")
PROPOSED = Proposed(
    tip=TIP,
    base=BASE,
    green=True,
    who_acts="merger",
    at=MOMENT,
    contract=contract.mark(task().task),
)
PULL = Pull(number=1, url="https://github.com/o/p/pull/1", title="Fix")
SEEN = PullSeen(
    number=1, url=PULL.url, title="Fix", state="open", head=TIP, base="main"
)
READ = MergeRead(tip=TIP, base=BASE, base_tree=TREE, verdict="merge", at=MOMENT)
MERGED = Merged(
    by="merger",
    via="session",
    commit=MERGE,
    merged_head=TIP,
    parent=BASE,
    destination="main",
    base_checked=BASE,
    base_merged=BASE,
    text_updated=False,
    at=MOMENT,
)
# Each point of the plain landing, as the landing's fields so far.
PREPARED = {
    "started": STARTED,
    "based": BASED,
    "checked": CHECKED,
    "reviews": (REVIEWED,),
    "filed": (FILED,),
}
OPENED = {
    **PREPARED,
    "phase": "open",
    "pushed": TIP,
    "proposed": PROPOSED,
    "pull": PULL,
}

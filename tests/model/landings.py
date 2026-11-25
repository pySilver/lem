"""Hypothesis strategies for the landing's rules: records and worlds built from the pieces of a
plain fast-track landing (`unit/landing/worlds.py`), each field drawn from its plain value and a
few others, so that a drawn case is near a real one and shrinks to it.

A status draws only the phases it can have (`landing.md` B): a landed task is past the merge, an
open one is in `open`, and a dropped or answered one is in any phase but `merged`.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.model.criteria import contract
from lem.model.landing import checks, merge_standing
from lem.model.landing.merge_asked import Asked
from lem.model.landing.merge_standing import digest_of
from lem.model.landing.world import Merger, PullSeen, Rules, World
from lem.records.landing.merge import MergeAccepted, MergeIntent, Refused
from lem.records.landing.propose import MergeRead, OwnerMerge, Standing
from lem.records.landing.record import Landing
from lem.records.landing.review import Finding, Reviewed
from lem.records.landing.start import Based, Resolution
from lem.records.task import Shape
from unit.landing.merges import MOVED, MOVED_TREE, alone
from unit.landing.worlds import (
    BASE,
    BRANCH,
    CHECKED,
    FILED,
    MERGE,
    MERGED,
    MOMENT,
    NIT,
    OPENED,
    OTHER,
    PREPARED,
    PROPOSED,
    PULL,
    READ,
    REVIEWED,
    SEEN,
    STARTED,
    TIP,
    TREE,
    task,
    world,
)

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record

# The bound keeps the level `model` near its aim of 60 s: its 49 cases took 50 s at a load
# average near 12 (2026-11-25, the owner's Mac). A fixed seed and no example database, so a run
# writes no `.hypothesis/` folder and a failure is the same on the next run.
LANDING = settings(
    max_examples=300,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=(HealthCheck.too_slow,),
)


# A commit a rebase makes, which no record names yet, and its tree.
NEW = "2" * 40
NEW_TREE = "d" * 40
SHAS = (TIP, OTHER, BASE, MOVED, NEW)
TREES = (TREE, MOVED_TREE, NEW_TREE)
EARLIER = MOMENT - timedelta(hours=1)
LATER = MOMENT + timedelta(hours=1)
MOMENTS = (MOMENT, EARLIER, LATER)
MUST = Finding(
    id="r1.2",
    level="must-fix",
    where="a.py",
    title="a must-fix",
    what="it",
    against="over",
)
OVER = replace(NIT, id="r1.3", against="over", title="an item over the bar")
# The statuses of the design's part 3, and the phases each may have a landing in.
PHASES = {
    "queued": (None,),
    "shaping": (None, "preparing"),
    "building": (None, "preparing"),
    "planned": (None, "preparing"),
    "ready": (None, "preparing"),
    "landing": ("preparing",),
    "open": ("open",),
    "landed": ("merged", "ended"),
    "dropped": (None, "preparing", "open", "ended"),
    "answered": (None, "preparing", "ended"),
}
ENDED = ("landed", "dropped", "answered")
MERGERS: tuple[Merger, ...] = ("merger", "owner")


def one_of[T](plain: T, *others: T) -> st.SearchStrategy[T]:
    """The plain value or one of `others`; a failing case shrinks toward the plain one."""
    return st.sampled_from((plain, *others))


def mostly[T](plain: T, *others: T) -> st.SearchStrategy[T]:
    """The plain value seven times in eight, else one of `others`: a case near the plain
    landing changes a few of its facts, not most of them (`one_of` over equal strategies
    draws as if they were one)."""
    return st.sampled_from((*(plain,) * 7, *others))


def checks_trees() -> st.SearchStrategy[str]:
    """The tree of the base the checks ran on: origin's base as the plain world has it, or
    another."""
    return st.sampled_from((TREE, TREE, TREE, MOVED_TREE, NEW_TREE))


def shas() -> st.SearchStrategy[str]:
    """A commit of the few a landing meets."""
    return st.sampled_from(SHAS)


def moments() -> st.SearchStrategy[datetime]:
    """The moment, an hour before it or an hour after it."""
    return st.sampled_from(MOMENTS)


@st.composite
def rules(draw: st.DrawFn) -> Rules:
    """The settings: who lands, how, the protected branches and the checks."""
    return Rules(
        base="main",
        land=draw(one_of("agent", "owner")),
        history=draw(one_of("squash", "keep")),
        protected=draw(one_of((), (BRANCH,), ("main",))),
        commands=draw(one_of(("true",), (), ("make",))),
        serial=draw(one_of((), ("make serial",))),
    )


@st.composite
def pulls(draw: st.DrawFn) -> PullSeen:
    """The pull request as the forge shows it: open, merged or closed, at a head, into a
    base, held in a queue or not, with what a merge reports or not."""
    return replace(
        SEEN,
        url=draw(one_of(PULL.url, "https://github.com/o/other/pull/1")),
        state=draw(one_of("open", "merged", "closed")),
        head=draw(shas()),
        base=draw(one_of("main", "release")),
        queued=draw(one_of(None, "in the merge queue")),
        merge_commit=draw(one_of(None, MERGE)),
        merged_head=draw(st.none() | shas()),
        base_parent=draw(st.none() | shas()),
    )


@st.composite
def worlds(draw: st.DrawFn) -> World:
    """The world of one moment, each fact its plain value or another."""
    return world(
        rules=draw(rules()),
        branch=draw(one_of(BRANCH, "main")),
        base=draw(shas()),
        base_tree=draw(st.sampled_from(TREES)),
        tip=draw(shas() | st.none()),
        tree=draw(st.sampled_from(TREES) | st.none()),
        clean=draw(st.booleans()),
        rebasing=draw(one_of(False, True)),
        base_in_tip=draw(st.booleans()),
        remote=draw(st.none() | shas()),
        remote_in_tip=draw(st.booleans()),
        local=draw(st.none() | shas()),
        local_in_base=draw(st.booleans()),
        pull=draw(st.none() | pulls()),
        candidates=tuple(draw(st.lists(pulls(), max_size=2))),
    )


@st.composite
def reviews(draw: st.DrawFn) -> Reviewed:
    """One review attempt: of a tip, answered or silent, with its findings and its call."""
    findings = draw(one_of((NIT,), (), (MUST,), (OVER,), (NIT, MUST)))
    return replace(
        REVIEWED,
        attempt=draw(st.integers(1, 4)),
        tip=draw(shas()),
        of=draw(one_of("change", "resolution")),
        scope=draw(one_of("whole", "resolution")),
        floor=draw(one_of("read", "round", "full")),
        kind=draw(one_of("read", "round", "full")),
        careful=draw(one_of(False, True, None)),
        answered=draw(one_of(("claude",), ())),
        findings=findings,
        to_file=tuple(
            finding.id for finding in findings if finding.level != "must-fix"
        ),
        at=draw(moments()),
    )


@st.composite
def reads(draw: st.DrawFn) -> MergeRead:
    """One read of the merge agent: a verdict or none, a call on a moved base or none."""
    return replace(
        READ,
        tip=draw(shas()),
        base=draw(shas()),
        base_tree=draw(st.sampled_from(TREES)),
        verdict=draw(one_of("merge", "call", None)),
        base_call=draw(one_of(None, "safe", "another round")),
        attempts=draw(st.integers(1, 2)),
        no_answer=draw(one_of(False, True)),
        at=draw(moments()),
    )


@st.composite
def landings(draw: st.DrawFn, phase: str) -> Landing:
    """A landing in `phase`, each step's evidence there or not, of one tip or another."""
    started = replace(
        STARTED,
        round=draw(st.integers(1, 3)),
        conflicting=draw(st.booleans()),
    )
    based = Based(
        tip=draw(shas()),
        base=draw(shas()),
        before=draw(shas()),
        carried=draw(st.booleans()),
        unshown_paths=draw(one_of((), ("a.py",))),
        at=draw(moments()),
    )
    checked = replace(
        CHECKED,
        tip=draw(shas()),
        base=draw(shas()),
        inputs=draw(one_of(CHECKED.inputs, checks.inputs(Rules(base="main")))),
        outcome=draw(one_of("passed", "red")),
        items_after=draw(one_of((), ("docs/backlog/an-item.md",))),
        at=draw(moments()),
    )
    resolution = Resolution(
        files=("a.py",),
        before=draw(shas()),
        after=draw(shas()),
        base=draw(shas()),
        read=draw(st.none() | st.integers(1, 3)),
    )
    proposed = replace(
        PROPOSED,
        tip=draw(shas()),
        base=draw(shas()),
        careful=draw(one_of(False, True)),
        reasons=draw(one_of((), ("the checks did not pass",))),
        who_acts=draw(one_of("merger", "owner")),
        owner_merge=draw(
            one_of(
                None,
                OwnerMerge(state="stands", why="the change and its reasons stay"),
                OwnerMerge(state="ended", why="the reasons it is not green changed"),
            )
        ),
        at=draw(moments()),
    )
    standing = Standing(
        tip=draw(shas()),
        reasons_digest=draw(
            one_of(
                digest_of(proposed.reasons, proposed.contract),
                digest_of(("x",), proposed.contract),
            )
        ),
        by_act="board",
        at=draw(moments()),
    )
    refused = Refused(
        tip=draw(shas()),
        source=draw(one_of("lem", "github")),
        kind=draw(one_of("rule", "tip", "base", "target")),
        line="refused",
        by=draw(one_of("merger", "owner")),
        at=MOMENT,
    )
    intent = MergeIntent(
        tip=draw(shas()), by=draw(one_of("merger", "owner")), via="server", at=MOMENT
    )
    accepted = MergeAccepted(tip=draw(shas()), at=MOMENT, queued="in the merge queue")
    kept = (
        ("started", started),
        ("based", based),
        ("checked", checked),
        ("resolution", resolution),
        ("proposed", proposed),
        ("standing", standing),
        ("refused", refused),
        ("intent", intent),
        ("accepted", accepted),
        ("merged", replace(MERGED, merged_head=draw(shas()))),
        ("pull", PULL),
    )
    fields = {name: value for name, value in kept if draw(st.booleans())}
    return replace(
        Landing(),
        round=draw(st.integers(1, 3)),
        relands=draw(st.integers(0, 2)),
        phase=phase,
        pushed=draw(st.none() | shas()),
        reviews=tuple(draw(st.lists(reviews(), max_size=3))),
        filed=draw(one_of((FILED,), ())),
        reads=tuple(draw(st.lists(reads(), max_size=3))),
        **fields,
    )


@st.composite
def records(draw: st.DrawFn, statuses: tuple[str, ...] = tuple(PHASES)) -> Record:
    """A fast-track or standard-track task in one of `statuses`, with a landing in a phase
    its status may have, its criteria approved by the owner or approved without him."""
    status = draw(st.sampled_from(statuses))
    phase = draw(st.sampled_from(PHASES[status]))
    made = draw(one_of(task(status), alone()))
    made = replace(made, task=replace(made.task, status=status))
    shape = Shape(
        type="docs",
        why="a word",
        track=draw(one_of("small", "full")),
        careful=draw(one_of((), ("the login",))),
    )
    made = replace(made, task=replace(made.task, shape=shape))
    if phase is None:
        return replace(made, landing=None)
    return replace(made, landing=draw(landings(phase)))


@st.composite
def opened_landings(draw: st.DrawFn) -> Record:
    """An open task near the plain one whose read says merge, or one the owner merges (not
    green, his merge standing for the base): each piece of evidence a merge reads kept, or
    changed one way."""
    landing = draw(landings("open"))
    plain = draw(mostly(task("open", **{**OPENED, "reads": (READ,)}), alone()))
    kept = plain.landing
    assert kept is not None
    seen = digest_of(merge_standing.reasons_now(plain), contract.mark(plain.task))
    stands = Standing(tip=TIP, reasons_digest=seen, by_act="board", at=MOMENT)
    safe = replace(READ, base=MOVED, base_tree=MOVED_TREE, base_call="safe")
    picks = {
        "pushed": draw(mostly(TIP, OTHER, None)),
        "proposed": draw(mostly(kept.proposed, landing.proposed)),
        "checked": draw(mostly(kept.checked, landing.checked)),
        "reviews": draw(mostly(kept.reviews, landing.reviews)),
        "reads": draw(
            one_of((READ,), (READ, safe), landing.reads, (*landing.reads, READ))
        ),
        "refused": draw(mostly(None, landing.refused)),
        "standing": draw(one_of(None, stands, landing.standing)),
        "pull": draw(mostly(PULL, None)),
    }
    return replace(plain, landing=replace(kept, **picks))


@st.composite
def facing_worlds(draw: st.DrawFn) -> World:
    """The world of an open pull request at the proposed tip, each fact a merge reads kept,
    or changed one way."""
    pull = replace(
        SEEN,
        state=draw(mostly("open", "merged", "closed")),
        head=draw(mostly(TIP, OTHER)),
        base=draw(mostly("main", "release")),
        url=draw(mostly(PULL.url, "https://github.com/o/other/pull/1")),
    )
    plain = world()
    return world(
        rules=draw(mostly(plain.rules, draw(rules()))),
        tip=draw(mostly(TIP, OTHER)),
        base=draw(mostly(BASE, MOVED)),
        base_tree=draw(mostly(TREE, MOVED_TREE)),
        pull=draw(mostly(pull, None)),
        remote=TIP,
        remote_in_tip=True,
    )


@st.composite
def asks(draw: st.DrawFn) -> Asked:
    """A merge asked for: the merge agent's, the owner's word for a tip, or his standing
    merge carried out by the server."""
    by = draw(st.sampled_from(MERGERS))
    standing = by == "owner" and draw(st.booleans())
    tip = (
        mostly(TIP, OTHER, "1234", None) if by == "owner" else mostly(None, TIP, OTHER)
    )
    return Asked(
        by=by,
        via=draw(one_of("server", "board", "session")),
        tip=draw(tip),
        standing=standing,
        subject=draw(mostly("docs: the login works", None)),
    )


# The plain landing's proposed tip, rebased by `base` onto a moved base an hour after its
# review: the tip `NEW`, which git's merge showed to keep the change.
CARRIED = Based(tip=NEW, base=MOVED, before=TIP, carried=True, at=LATER)


@st.composite
def moved_landings(draw: st.DrawFn) -> Landing:
    """An open landing whose proposed tip a rebase or a builder's resolution moved onto the
    tip `NEW`: the rebase shown or not, the read a real verdict or not, the resolution read
    clean or not, each kept or changed one way."""
    read = replace(
        READ,
        verdict=draw(mostly("merge", "call", None)),
        no_answer=draw(mostly(False, True)),
    )
    resolved = replace(
        REVIEWED,
        attempt=2,
        tip=NEW,
        of="resolution",
        scope="resolution",
        findings=draw(mostly((), (NIT,), (MUST,))),
        to_file=(),
        careful=draw(mostly(False, True, None)),
        answered=draw(mostly(("claude",), ())),
    )
    resolution = Resolution(
        files=("a.py",),
        before=draw(mostly(TIP, OTHER)),
        after=draw(mostly(NEW, OTHER)),
        base=draw(mostly(MOVED, BASE)),
        read=draw(mostly(2, None)),
    )
    first = replace(REVIEWED, findings=draw(mostly((NIT,), (MUST,))))
    return replace(
        Landing(),
        phase="open",
        proposed=PROPOSED,
        reads=(read,),
        reviews=(first, resolved),
        based=replace(
            CARRIED,
            carried=draw(mostly(True, False)),
            tip=draw(mostly(NEW, OTHER)),
            at=draw(mostly(LATER, EARLIER)),
        ),
        resolution=draw(mostly(resolution, None)),
    )


@st.composite
def moved_worlds(draw: st.DrawFn) -> World:
    """The world after the rebase, the tip `NEW` on the moved base, or a world drawn."""
    if draw(mostly(True, False)):
        return world(tip=NEW, base=MOVED, base_tree=MOVED_TREE)
    return draw(worlds())


# The steps of `preparing` in their order, as the plain landing's fields they leave.
STEPS = ("started", "based", "checked", "reviews", "filed")


@st.composite
def near_records(
    draw: st.DrawFn, statuses: tuple[str, ...] = ("landing", "landing", "open", "ready")
) -> Record:
    """A task near the plain landing: ready, at a point of `preparing` (of its first round, or
    of a new one), or open (one of `statuses`, each as often as it is named), with each piece
    of evidence kept, or changed one way."""
    status = draw(st.sampled_from(statuses))
    other = draw(landings("open" if status == "open" else "preparing"))
    point = draw(st.sampled_from(range(len(STEPS) + 1)))
    plain = {**OPENED, "reads": (READ,)} if status == "open" else dict(PREPARED)
    if status != "open" and draw(st.booleans()):
        # A new round, its evidence whole, whose tip is the one proposed before, as the
        # forge holds it.
        again = {"round": 2, "relands": 1, "started": replace(STARTED, round=2)}
        plain |= {**again, "proposed": PROPOSED, "pushed": TIP, "pull": PULL}
    else:
        for name in STEPS[point:] if status != "open" else ():
            plain.pop(name)
    for name in (*STEPS, "proposed", "pushed", "reads", "pull"):
        if draw(mostly(False, True)):
            plain[name] = getattr(other, name)
    made = task(status, **plain)
    shape = Shape(type="docs", why="a word", track=draw(mostly("small", "full")))
    return replace(made, task=replace(made.task, shape=shape))


@st.composite
def near_worlds(draw: st.DrawFn) -> World:
    """The world of the plain landing, each fact kept, or changed one way."""
    plain = world()
    pull = draw(one_of(None, SEEN, replace(SEEN, head=OTHER), draw(pulls())))
    return replace(
        plain,
        rules=draw(mostly(plain.rules, draw(rules()))),
        base=draw(mostly(plain.base, MOVED)),
        base_tree=draw(mostly(plain.base_tree, MOVED_TREE)),
        tip=draw(mostly(plain.tip, OTHER, BASE)),
        clean=draw(mostly(True, False)),
        rebasing=draw(mostly(False, True)),
        base_in_tip=draw(mostly(True, False)),
        remote=draw(mostly(None, TIP, OTHER)),
        remote_in_tip=draw(mostly(True, False)),
        pull=pull,
        candidates=draw(mostly((), (SEEN,), (replace(SEEN, head=OTHER),))),
    )


def any_records() -> st.SearchStrategy[Record]:
    """A drawn task, in any status, or near the plain landing."""
    return records() | near_records()


def any_worlds() -> st.SearchStrategy[World]:
    """A drawn world, or one near the plain landing's."""
    return worlds() | near_worlds()


@st.composite
def must_fixed(draw: st.DrawFn) -> Record:
    """A drawn task whose newest review answered and left a must-fix, of the tip now or
    another, as a carry may have moved it."""
    record = draw(any_records())
    landing = record.landing or Landing()
    left = replace(
        REVIEWED,
        attempt=len(landing.reviews) + 1,
        tip=draw(shas()),
        findings=draw(one_of((MUST,), (NIT, MUST), (MUST, MUST))),
        at=draw(moments()),
    )
    reviews = (*landing.reviews, left)
    return replace(record, landing=replace(landing, reviews=reviews))

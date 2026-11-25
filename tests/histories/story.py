"""A landing told one step at a time against the model, with no git and no forge: the record,
the world and the forge's calls, each step decided by `model/landing` and written into the
record as its command writes it, and its effect made on the world (the design's part 8, the
level `histories`).

A step's record and its effect are apart, so that a history can cut a step off between them:
`effect` changes the world alone, `write` the record alone. Each forge call is one line of
`calls`, and each line for the owner (a refusal's why, the due step's why) one of `said`.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import (
    base,
    base_kept,
    begin,
    checks,
    clean,
    filing,
    merge,
    mergeread,
    phases,
    propose,
    reconcile,
    review,
    start,
)
from lem.model.landing.clean import Facts as GitFacts
from lem.model.landing.clean import Sweep
from lem.model.landing.filing_flags import Flags
from lem.model.landing.filing_place import Shelf
from lem.model.landing.mergeread import Briefed
from lem.model.landing.propose_facts import Facts
from lem.model.landing.review_due import Facts as ReviewFacts
from lem.model.landing.review_said import Outside, Said
from lem.records.landing.checks import Checked
from lem.records.landing.merge import MergeAccepted, Merged
from lem.records.landing.record import Landing, Pull
from unit.landing.merges import MOVED, MOVED_TREE, SAME
from unit.landing.worlds import MERGE, SEEN, TREE, task, world

if TYPE_CHECKING:
    from lem.model.landing.merge_asked import Asked
    from lem.model.landing.propose import Proposal
    from lem.model.landing.reconcile import Trees
    from lem.model.landing.world import Due, World
    from lem.records.landing.start import Based
    from lem.records.record import Record

# The commit a rebase onto the moved base makes of the tip, and its tree.
REBASED = "2" * 40
REBASED_TREE = "d" * 40
# The tree of the base the checks ran on, as the merge reads it from git.
CHECKS_TREE = TREE
WHERE = "/work/fix-the-login"
TITLE = "docs: the login works"
NOTES = "none\n"


# A defect the review saw outside the change, cheap: a line of the pull request.
CHEAP = Outside(
    where="docs/login.md",
    title="a word is misspelled",
    what="line 3 says `logn`",
    against="cheap",
    why="one word",
)


def answered(tip: str, *, attempt: int = 1, careful: bool = False) -> Said:
    """A review that answered, saw one cheap defect outside the change, and made the careful
    call."""
    return Said(
        attempt=attempt,
        tip=tip,
        kind="read",
        answered=("claude",),
        outside=(CHEAP,),
        careful=careful,
        careful_why="it reaches no topic of the project's",
    )


@dataclass
class Story:
    """One landing: the record, the world, the forge's calls and the owner's lines so far."""

    record: Record = field(default_factory=lambda: task("ready"))
    world: World = field(default_factory=world)
    calls: list[str] = field(default_factory=list)
    said: list[str] = field(default_factory=list)

    @property
    def landing(self) -> Landing:
        """The landing on record."""
        return self.record.landing or Landing()

    def due(self) -> Due:
        """The step due now, its why said to the owner."""
        found = phases.due(self.record, self.world)
        self.said.append(found.why)
        return found

    def refused(self, found: object) -> Refusal:
        """A refusal the owner reads."""
        assert isinstance(found, Refusal), found
        self.said.append(found.why)
        return found

    def write(self, **fields: object) -> None:
        """The landing's `fields` written into the record."""
        self.record = replace(self.record, landing=replace(self.landing, **fields))

    def effect(self, **facts: object) -> None:
        """The world with `facts` changed."""
        self.world = replace(self.world, **facts)

    def moved(self, status: str) -> None:
        """The task in `status`."""
        self.record = replace(
            self.record, task=replace(self.record.task, status=status)
        )

    # ---- preparing ----

    def start(self, *, conflicting: bool = False) -> None:
        """`start`: the round begins, the task `landing`."""
        facts = start.Facts()
        found = start.decide(self.record, self.world, facts, conflicting=conflicting)
        assert not isinstance(found, Refusal), found
        self.record = begin.begun(self.record, found)

    def rebase(self) -> None:
        """`base`'s effect: the tip rebased onto origin's base, which git's merge of the tip
        before showed to keep the change."""
        self.effect(
            tip=REBASED,
            tree=REBASED_TREE,
            local=REBASED,
            base_in_tip=True,
        )

    def base(self) -> Based:
        """`base`: the branch put on origin's base, rebased when the tip lacks it; the review
        carries over a rebase git showed."""
        facts = base.Facts(ahead=1)
        move = base.decide(self.record, self.world, facts, WHERE)
        assert not isinstance(move, Refusal), move
        before = self.world.tip
        if move == "rebase":
            self.rebase()
        tree = self.world.tree or REBASED_TREE
        merged = tree if move == "rebase" else None
        after = base.After(
            tip=self.world.tip or REBASED,
            tree=tree,
            ahead=1,
            merged=merged,
            reviewed=merged,
            before=before,
        )
        based = base.judged(self.world, after)
        self.record = base_kept.kept(self.record, based, None)
        return based

    def checks(self) -> None:
        """`checks`: the commands run on the tip, passed, written down."""
        assert checks.decide(self.record, self.world) is None
        made = Checked(
            tip=self.world.tip or "",
            tree=self.world.tree or "",
            base=self.world.base,
            inputs=checks.inputs(self.world.rules),
            outcome="passed",
            at=self.world.now,
        )
        self.write(checked=made)

    def read(self, said: Said | None = None) -> None:
        """`read --record`: the review of the tip written down."""
        attempt = len(self.landing.reviews) + 1
        made = said or answered(self.world.tip or "", attempt=attempt)
        found = review.decide(self.record, self.world, made, ReviewFacts())
        assert not isinstance(found, Refusal), found
        self.write(reviews=(*self.landing.reviews, found))

    def file(self) -> None:
        """`file`: each defect outside the change gets its place; none here needs an item."""
        shelf = Shelf(folder="docs/backlog")
        found = filing.decide(self.record, self.world, shelf, Flags())
        assert not isinstance(found, Refusal), found
        assert not found.writes
        self.write(filed=(*self.landing.filed, *found.filed))

    def proposal(self, notes: str = NOTES) -> Proposal | Refusal:
        """What `propose` decides now."""
        facts = Facts(notes=notes)
        return propose.decide(self.record, self.world, facts, TITLE)

    def push(self, proposal: Proposal) -> None:
        """`propose`'s push, recorded before the forge's call, and the push itself."""
        tip = self.world.tip or ""
        self.write(pushed=tip)
        if proposal.push:
            self.calls.append(f"push {tip}")
            self.effect(remote=tip, remote_in_tip=True)

    def request(self, proposal: Proposal, *, on_record: bool = True) -> None:
        """`propose`'s pull request: the one on the branch adopted and edited, or a new one.
        Until the record names it (`on_record`), the forge shows it as one open on the
        branch."""
        tip = self.world.tip or ""
        if proposal.adopt is None:
            self.calls.append("create pull request")
        else:
            self.calls.append(f"edit pull request {proposal.adopt.number}")
        made = replace(SEEN, head=tip)
        if on_record:
            self.effect(pull=made, candidates=())
        else:
            self.effect(pull=None, candidates=(made,))

    def propose(self, notes: str = NOTES) -> Proposal:
        """`propose` whole: its push, its pull request and its record."""
        found = self.proposal(notes)
        assert not isinstance(found, Refusal), found
        self.push(found)
        self.request(found)
        self.opened(found)
        return found

    def opened(self, proposal: Proposal) -> None:
        """`propose`'s record: the proposal, the pull request and the task open."""
        pull = Pull(number=SEEN.number, url=SEEN.url, title=SEEN.title)
        self.write(proposed=proposal.proposed, pull=pull, phase="open")
        self.moved("open")

    # ---- open ----

    def briefed(self) -> Briefed:
        """The brief of the merge agent's read of the proposal on origin's base now."""
        proposed = self.landing.proposed
        assert proposed is not None
        checked = self.landing.checked
        moved = checked is not None and self.world.base != checked.base
        return Briefed(
            tip=proposed.tip,
            base=self.world.base,
            base_tree=self.world.base_tree,
            moved=moved,
        )

    def merge_review(self, reply: str | None) -> None:
        """`merge-review`: the merge agent's reply written down."""
        found = mergeread.decide(self.record, self.briefed(), reply, self.world.now)
        assert not isinstance(found, Refusal), found
        self.write(reads=(*self.landing.reads, found))

    def merge(self, asked: Asked, checks_tree: str = CHECKS_TREE) -> None:
        """`merge` up to its call: the intent written under the merge lock, then the call."""
        found = merge.decide(self.record, self.world, asked, checks_tree)
        assert not isinstance(found, Refusal), found
        self.write(intent=found.intent)
        self.calls.append(f"merge {found.method} {found.intent.tip}")

    def forge_merged(self) -> None:
        """The forge's merge of the request at its head, onto origin's base now."""
        pull = self.world.pull
        assert pull is not None
        done = replace(
            pull,
            state="merged",
            merge_commit=MERGE,
            merged_head=pull.head,
            base_parent=self.world.base,
        )
        self.effect(pull=done, base=MERGE)

    def reconcile(self, trees: Trees = SAME) -> None:
        """The intent on record replaced by what the forge shows; kept, and the owner told,
        while only an open request is visible."""
        intent = self.landing.intent
        assert intent is not None
        found = reconcile.reconciled(self.record, self.world, intent, trees)
        if isinstance(found, Refusal):
            self.said.append(found.why)
            return
        if found is None:
            self.write(intent=None, accepted=None)
            self.moved("dropped")
        elif isinstance(found, Merged):
            self.write(merged=found, intent=None, accepted=None, phase="merged")
        elif isinstance(found, MergeAccepted):
            self.write(accepted=found, intent=None)
        else:
            self.write(refused=found, intent=None, accepted=None)

    def merged(self) -> None:
        """`merged`'s bookkeeping: the task landed."""
        assert self.landing.merged is not None
        self.moved("landed")

    def clean(self, facts: GitFacts | None = None) -> Sweep:
        """`clean`: what goes, gone, and the landing ended."""
        found = clean.decide(self.record, self.world, facts or GitFacts())
        assert not isinstance(found, Refusal), found
        if found.remote is not None:
            self.calls.append(f"delete {self.world.branch} at {found.remote}")
        self.effect(
            tip=None,
            tree=None,
            local=self.world.local if found.branch_left else None,
        )
        self.write(phase="ended")
        return found

    def base_moved(self) -> None:
        """A teammate's merge moved origin's base to another tree."""
        self.effect(base=MOVED, base_tree=MOVED_TREE, base_in_tip=False)


def opened(*, read: bool = True) -> Story:
    """The plain landing open, with its read saying merge or with none yet."""
    story = Story()
    for act in (story.start, story.base, story.checks, story.read, story.file):
        act()
    story.propose()
    if read:
        story.merge_review("Verdict: merge. One word of the docs.")
    return story

"""A run of the checks from its first command to its verdict (`land.checks_body` on `main`): the
stale bytecode removed, the commands and then the serial ones, what they left removed, and the
judgment in its order: red commands, a changed tree, the criteria's check, the bar. A stop and a
refusal of the run itself end it as stopped or refused, with what it found so far.
"""

import contextlib
import dataclasses
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import (
    checks_bar,
    checks_git,
    checks_judge,
    checks_output,
    checks_run,
    checks_tree,
    frame,
)
from lem.kernel.errors import Refusal
from lem.model.criteria import contract
from lem.model.landing import bar, checks, checks_ended, checks_said
from lem.records.landing.checks import Checked, Outcome, Removed
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Generator

    from lem.records.base import Moment

PASSED: checks_said.Ending = "passed"


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Verdict:
    """How a run ended: the run as the record keeps it, the refusal the step exits with, what
    the checks refused in the owner's words, whether the fast track takes the standard one,
    the mark of the contract the run was of (`model/criteria/contract.py`), and how long it
    ran by a clock no change of the wall clock moves (`land.checks_run` on `main`)."""

    run: Checked
    refusal: Refusal | None = None
    refused: str | None = None
    reshape: bool = False
    contract: str | None = None
    seconds: int | None = None


def commands_of(context: frame.Context) -> tuple[Outcome, ...]:
    """The commands' outcomes, then the serial ones' when every command passed."""
    outcomes = checks_run.every(context)
    if all(outcome.passed for outcome in outcomes):
        return (*outcomes, *checks_run.serials(context))
    return outcomes


@dataclasses.dataclass(kw_only=True, slots=True)
class Evidence:
    """The run as it goes: its context and start, the mark of the contract it is of, taken
    before its first command, the evidence found so far, and the stale bytecode it removed."""

    context: frame.Context
    began: Moment
    contract: str | None = None
    found: Checked | None = None
    bytecode: tuple[str, ...] = ()

    def evidence(self, outcome: checks_said.Ending, **fields: object) -> Checked:
        """The run with `outcome` and `fields` over what was found so far."""
        world = self.context.world
        task = self.context.record.task
        plan = task.plan.path if task.plan else None
        found = self.found or Checked(
            tip=world.tip or "",
            tree=world.tree or "",
            base=world.base,
            inputs=checks.inputs(world.rules, plan),
            criteria_digest=task.criteria.digest,
            own_checks=world.rules.own_checks,
            outcome=outcome,
            at=self.began,
        )
        self.found = replace(found, outcome=outcome, **fields)
        return self.found

    @contextlib.contextmanager
    def swept(self) -> Generator[None]:
        """What git does not know before the first command stays; what the commands left that
        git neither tracks nor ignores goes after them, however they end, and is named."""
        worktree = self.context.worktree
        there = checks_git.untracked(worktree)
        try:
            yield
        finally:
            self.left(checks_tree.swept(worktree, there))

    def left(self, gone: tuple[str, ...]) -> None:
        """What the run removed from the worktree, before and after its commands."""
        self.evidence(PASSED, removed=Removed(untracked=gone, bytecode=self.bytecode))

    def commanded(self) -> tuple[Outcome, ...]:
        """The stale bytecode removed, the commands run, and what they left removed."""
        worktree, slug = self.context.worktree, self.context.record.task.slug
        self.bytecode = checks_tree.cleared(worktree, slug)
        with self.swept():
            outcomes = commands_of(self.context)
            self.evidence(PASSED, outcomes=outcomes)
        return outcomes


@dataclasses.dataclass(kw_only=True, slots=True)
class Judgment(Evidence):
    """The run and its judgment, in their order."""

    def ran(self) -> Verdict:
        """The commands, and the judgment."""
        outcomes = self.commanded()
        failed = tuple(outcome.command for outcome in outcomes if not outcome.passed)
        if failed:
            return Verdict(run=self.evidence("red"), refusal=checks_ended.red(failed))
        return self.judged()

    def judged(self) -> Verdict:
        """What no command of the project checks: the tree, the criteria, the bar."""
        tip = self.context.world.tip or ""
        refusal = checks_judge.tree_refusal(self.context, tip)
        if refusal is not None:
            return self.refused(
                refusal, "a command of the checks changed what git tracks"
            )
        moved = self.reread()
        if moved is not None:
            return self.refused(moved, "the criteria changed while the checks ran")
        red, taken = checks_judge.criteria_run(self.context, self.began)
        self.evidence(PASSED, criteria=checks_judge.criteria_of(red, taken))
        refusal = checks_judge.criteria_refusal(red)
        if refusal is not None:
            return self.refused(refusal, "the check of the criteria did not pass")
        return self.barred(tip)

    def reread(self) -> Refusal | None:
        """Read the record again after the commands: the criteria's check is of the criteria
        as they are now, and refused when they changed since the run began."""
        context = self.context
        now = tasks.read(context.workspace.state, context.record.task.slug)
        seen = context.record.task.criteria
        refused = contract.moved(now.task, self.contract)
        refused = refused or checks.moved(seen, now.task.criteria)
        self.context = dataclasses.replace(context, record=now)
        return refused

    def barred(self, tip: str) -> Verdict:
        """The bar and the size; a lowered bar with no reason is refused, and on the fast
        track the task takes the standard one."""
        context = self.context
        base = merge_base(context, tip)
        found = checks_bar.lowered_of(context, base, tip)
        size = checks_bar.size_of(context, base, tip)
        self.evidence(
            PASSED,
            bar_base=base,
            lowered=checks_bar.kept_marks(found),
            edited=found.edited,
            not_covered=found.not_covered,
            size=size,
        )
        return self.lowered(found)

    def lowered(self, found: bar.BarRead) -> Verdict:
        """Passed, or refused for a bar lowered with no reason."""
        small = checks_judge.small(self.context.record)
        refusal = bar.refusal(found.lowered, small=small)
        if refusal is None:
            return Verdict(run=self.evidence(PASSED))
        said = "the change lowers the bar with no reason given"
        return dataclasses.replace(self.refused(refusal, said), reshape=small)

    def stopped(self) -> Verdict:
        """A stop: what ran is ended with what it started, and the run is kept as stopped."""
        slug = self.context.record.task.slug
        refusal = Refusal(
            "stopped",
            "the checks were stopped, and the command that ran is ended with what it started",
            f"`lem land checks {slug}` runs them again",
        )
        return Verdict(run=self.evidence("stopped"), refusal=refusal)

    def refused(self, refusal: Refusal, said: str) -> Verdict:
        """The run refused, with what it found so far."""
        return Verdict(run=self.evidence("refused"), refusal=refusal, refused=said)


def merge_base(context: frame.Context, tip: str) -> str:
    """Where the change starts: the merge base of the tip and origin's base."""
    base = context.world.base
    return context.ports.git.merge_base(context.worktree, tip, base) or base


def judged(context: frame.Context, began: Moment) -> Verdict:
    """The run and its verdict, with the mark of the contract it was of; a stop ends it as
    stopped, a refusal of the run as refused."""
    mark = contract.mark(context.record.task)
    judgment = Judgment(context=context, began=began, contract=mark)
    try:
        verdict = judgment.ran()
    except checks_output.Cut as cut:
        earlier = judgment.found.outcomes if judgment.found else ()
        judgment.evidence("stopped", outcomes=(*earlier, *cut.outcomes))
        verdict = judgment.stopped()
    except InterruptedError:
        verdict = judgment.stopped()
    except Refusal as refusal:
        verdict = judgment.refused(refusal, refusal.why)
    return dataclasses.replace(verdict, contract=mark)

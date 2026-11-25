"""The check that each criterion's tests pass on the branch and fail on the base
(`criteria.cmd_red` on `main`)."""

from lem.records.base import Frozen, Moment, Sha


class RedTest(Frozen, frozen=True, kw_only=True):
    """One test of one criterion, run on both sides: the exit codes, and what went wrong."""

    criterion: int
    command: str
    files: tuple[str, ...] = ()
    on_branch: int | None = None
    on_base: int | None = None
    problem: str | None = None


class WithoutTest(Frozen, frozen=True, kw_only=True):
    """A criterion with no test, and why."""

    criterion: int
    why: str


class SetupRun(Frozen, frozen=True, kw_only=True):
    """A setup command's run on one side, with its exit, failed or not (`cmd_red` on `main`
    printed each)."""

    on: str
    command: str
    exit: int


class Inputs(Frozen, frozen=True, kw_only=True):
    """The five inputs of a run: the tip and the base as full shas (a view shortens them), the
    plan's path (None on the fast track), the setup and the serial commands."""

    tip: Sha
    base: Sha
    plan: str | None = None
    setup: tuple[str, ...] = ()
    serial: tuple[str, ...] = ()


class Red(Frozen, frozen=True, kw_only=True):
    """One run of the check: whether it holds, its tests, the criteria without a test, the
    changed files not laid over the base, every setup run, and the inputs."""

    ok: bool
    at: Moment
    digest: str
    inputs: Inputs
    tests: tuple[RedTest, ...] = ()
    without_a_test: tuple[WithoutTest, ...] = ()
    run_without: tuple[str, ...] = ()
    setup: tuple[SetupRun, ...] = ()

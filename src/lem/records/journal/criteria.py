"""The journal's entry of a run of the checks whose commands passed: the start of its check of
the criteria."""

from lem.records.base import Moment, Sha, Tagged


class CriteriaRun(Tagged, tag="criteria-run", frozen=True, kw_only=True):
    """The checks' commands passed on `tip`, and the check of the criteria begins: their tests
    run, or the polish pass's run of them at `taken` is taken. The Timeline says which while
    the run goes on (`main` drew it from the gate events and the pass)."""

    at: Moment
    tip: Sha
    taken: Sha | None = None

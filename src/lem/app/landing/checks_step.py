"""The step `lem land checks`, from its refusals before the first command to its record (`land.
cmd_checks` and `checks_run` on `main`).

Before anything runs: a command to run, the polish pass in the tip, and the load gate
(`checks_ready.py`). Then the commands, the serial ones when the others passed, and the judgment
(`checks_verdict.py`). A term from `--stop` holds from the gate to the judgment
(`checks_stop.py`): it ends what runs, and the run is kept as stopped; once the run is judged
the handler still holds, so that a term changes nothing and the result is kept whole. A refusal
of the run itself ends it as refused. Each end is one `CheckEnd` in the journal, with the run on
record and the checks' span ended.
"""

import time
from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import (
    checks_kept,
    checks_ready,
    checks_stop,
    checks_verdict,
    step,
)
from lem.kernel import clock

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing import frame
    from lem.kernel.envelope import Envelope
    from lem.records.landing.checks import Checked


def act(context: frame.Context) -> Checked:
    """Run the checks on the tip, and record the run."""
    checks_ready.ready(context)
    stopper = checks_stop.Stopper()
    with stopper.held():
        checks_ready.gated(context)
        began, ticked = clock.now(), time.monotonic()
        checks_ready.written(context, partial(checks_ready.began, at=began))
        verdict = checks_kept.timed(checks_verdict.judged(context, began), ticked)
        stopper.done = True
        keep = partial(checks_kept.kept, world=context.world, verdict=verdict)
        checks_ready.written(context, partial(keep, at=clock.now()))
    if verdict.refusal is not None:
        raise verdict.refusal
    return verdict.run


def run(folder: Path, slug: str) -> Envelope:
    """`lem land checks SLUG`."""
    return step.landed(folder, slug, "checks", act)

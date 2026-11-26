"""Why a step of a task may not run now: the step lock's refusals (`land.held_refusal` and
`land.step_lock` on `main`), with the way on each names."""

import shlex
from typing import TYPE_CHECKING

from lem.kernel import clock
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.steps import Holder


def held_why(slug: str, step: str, holder: Holder) -> str:
    """Why `step` waits for the step that holds the lock (`land.held_refusal` on `main`)."""
    since = clock.minute(holder.since)
    when = f"since {since}, in process {holder.pid}"
    status = f"`lem land checks {slug} --status` says whether they still run"
    if holder.step == "checks" and step == "checks":
        return (
            f"the checks of {slug} already run ({when}): a second run is refused. The "
            f"session that started them goes on when they end; {status}"
        )
    if holder.step == "checks":
        return (
            f"the checks of {slug} run ({when}), and their end comes first: the session "
            f"that started them goes on when they end, and this step waits for it; {status}"
        )
    return f"another step of {slug} runs now, `lem land {holder.step} {slug}` ({when})"


def refusal(slug: str, step: str, holder: Holder | None) -> Refusal:
    """The refusal of `step` while another holds the lock."""
    if holder is None:
        why = f"another step of {slug} runs now and holds its lock (step.lock)"
    else:
        why = held_why(slug, step, holder)
    return Refusal(
        "step-held", why, f"wait for it to end, then run lem land {step} {slug} again"
    )


def unopened(path: Path, slug: str, step: str, error: OSError) -> Refusal:
    """The refusal of a step whose lock file cannot be opened (`land.step_lock` on `main`)."""
    return Refusal(
        "step-lock",
        f"the step lock {path} cannot be opened ({error.strerror})",
        f"it holds no state: remove it (rm -r {shlex.quote(str(path))}), then run lem land "
        f"{step} {slug} again",
    )

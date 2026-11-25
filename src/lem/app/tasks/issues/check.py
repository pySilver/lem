"""`lem issue check`: whether origin's issues can be Lem's tracker. It writes nothing and needs
no `[tracker]` table, so onboarding runs it before the table is written. Each missing thing is
refused with its fix; with nothing missing, the facts onboarding needs and one line."""

from typing import TYPE_CHECKING

from lem.app.tasks.issues import facts
from lem.app.tasks.issues.results import enveloped
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    import msgspec

    from lem.app.wiring import Ports
    from lem.kernel.envelope import Envelope


def check(ports: Ports) -> Envelope | msgspec.Struct:
    """The tracker's check, or the refusal that names each missing thing and its fix."""
    found = facts.of(ports).check()
    if found.missing:
        raise Refusal(
            "tracker-check",
            "; ".join(missing.what for missing in found.missing),
            "; ".join(missing.fix for missing in found.missing),
        )
    held = "holds at least one issue" if found.has_issues else "holds no issue yet"
    say = (
        f"the issues of {found.repository} are on, and gh is signed in: Lem can read and "
        f"write them; the repository {held}"
    )
    return enveloped(found, say)

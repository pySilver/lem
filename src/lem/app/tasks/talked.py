"""`lem task talked`: the plan talk's counts, which the landing reads and the pull request
shows, with the bound of turns its rules give, so that a reader says when the talk went over
it. It ends the talk's span, which `lem task span SLUG plan-talk start --by AGENT` began."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import talk as rule
from lem.records.base import Frozen
from lem.records.work import Talk
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path


class Talked(Frozen, frozen=True, kw_only=True):
    """The talk written, and the most turns its rules give it."""

    slug: str
    talk: Talk
    bound: int


def talked(state: Path, slug: str, counts: Talk) -> Talked:
    """Write the plan talk's `counts` on the task `slug`, at this moment."""
    record = release.checked(state, slug)
    talk = replace(counts, at=clock.now())
    tasks.update(state, slug, partial(rule.talked, talk=talk), record.revision)
    return Talked(slug=slug, talk=talk, bound=rule.bound(talk))

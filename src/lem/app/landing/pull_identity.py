"""Check what the forge returns by number before using it as the task's pull request."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import world as facts
from lem.model.landing.destination import same_pull

if TYPE_CHECKING:
    from lem.ports.forge import Forge
    from lem.ports.forge_facts import Pull
    from lem.records.base import Sha
    from lem.records.landing.start import Started
    from lem.records.record import Record


def checked(record: Record, pull: Pull) -> Pull:
    """Keep the forge's facts only when they belong to the pull request on record."""
    wrong = same_pull(record, (pull.number, pull.url))
    if wrong is not None:
        raise wrong
    return pull


def matches(pull: Pull, started: Started, pushed: Sha) -> bool:
    """Whether the forge merged this landing's branch, push and destination."""
    return (
        pull.state == "merged"
        and pull.head_ref == started.branch
        and pull.merged_head == pushed
        and pull.base == started.base_ref
    )


def in_repo(pull: Pull, repo: str) -> bool:
    """The pull request's address names the configured repository and its number."""
    number = pull.number
    return pull.url == f"{repo}/pull/{number}"


def recovered(forge: Forge, started: Started, pushed: Sha) -> Pull | None:
    """Find the merged pull request when the stop after a push lost its number."""
    found = forge.find_pulls(started.branch, started.base_ref)
    matching = tuple(pull for pull in found if matches(pull, started, pushed))
    if not matching:
        return None
    repo = forge.repo().url.rstrip("/")
    own = tuple(pull for pull in matching if in_repo(pull, repo))
    if len(own) > 1:
        raise Refusal(
            "ambiguous-pull",
            f"the forge shows more than one merge of {started.branch} at {pushed}",
            "the owner checks the matching pull requests on GitHub before the task ends",
        )
    return next(iter(own), None)


def seen(pull: Pull) -> facts.PullSeen:
    """A pull request as the landing reads it."""
    return facts.PullSeen(
        number=pull.number,
        url=pull.url,
        title=pull.title,
        body=pull.body,
        state=pull.state,
        head=pull.head,
        base=pull.base,
        queued=pull.queued,
        dequeued=pull.dequeued,
        queue_event=pull.queue_event,
        queue_entered=pull.queue_entered,
        merge_commit=pull.merge_commit,
        merged_head=pull.merged_head,
        base_parent=pull.base_parent,
    )


def in_world(forge: Forge, record: Record, world: facts.World) -> facts.World:
    """The pull request on record, by its number; with none on record, every open one on the
    task's branch, which `propose` judges (`model/landing/propose.adopted`)."""
    landing = record.landing
    if landing is not None and landing.pull is not None:
        pull = checked(record, forge.pull(landing.pull.number))
        return replace(world, pull=seen(pull))
    found = forge.find_pulls(world.branch, world.rules.base)
    candidates = tuple(seen(pull) for pull in found if pull.state == "open")
    return replace(world, candidates=candidates)

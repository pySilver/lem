"""A pull request's current queue entry and its latest queue event on GitHub."""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters.forge_gh_queue_packet import QueueView, Response
from lem.adapters.forge_gh_shell import Oid
from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from datetime import datetime

    from lem.adapters.forge_gh_shell import Gh

QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      mergeQueueEntry { headCommit { oid } }
      timelineItems(last: 1, itemTypes: [
        ADDED_TO_MERGE_QUEUE_EVENT, REMOVED_FROM_MERGE_QUEUE_EVENT
      ]) {
        nodes {
          __typename
          ... on RemovedFromMergeQueueEvent { createdAt reason beforeCommit { oid } }
        }
      }
    }
  }
}
"""


class QueueFacts(msgspec.Struct, frozen=True, kw_only=True):
    """The queue's word for the submitted head or why it removed it."""

    queued: str | None = None
    dequeued: str | None = None


def viewed(gh: Gh, number: int) -> QueueView:
    """Read the queue evidence for the pull request in the configured repository."""
    owner, repo = gh.named().split("/", 1)
    said = gh.said(
        "api",
        "graphql",
        "-f",
        f"query={QUERY}",
        "-f",
        f"owner={owner}",
        "-f",
        f"repo={repo}",
        "-F",
        f"number={number}",
    )
    repository = msgspec.json.decode(said, type=Response).response.get("repository")
    if repository is None or repository.pull_request is None:
        raise Unanswered(
            "gh", "GitHub returned no pull request for the merge queue query"
        )
    return repository.pull_request


def queue(gh: Gh, number: int, tip: str, since: datetime) -> QueueFacts:
    """Accept only queue evidence for the submitted head and the current call."""
    found = viewed(gh, number)
    entry = found.merge_queue_entry
    if entry is not None:
        head = entry.head_commit
        return QueueFacts(
            queued="the merge queue" if head and head.oid == tip else None
        )
    newest = next(iter(found.timeline_items.nodes), None)
    if newest is None or newest.typename != "RemovedFromMergeQueueEvent":
        return QueueFacts()
    if (
        newest.created_at is not None
        and newest.created_at >= since
        and newest.before_commit == Oid(tip)
    ):
        return QueueFacts(dequeued=newest.reason)
    return QueueFacts()

"""GitHub's latest queue event and the entry it still holds, read together."""

from typing import TYPE_CHECKING

import msgspec

from lem.model.landing.queue_evidence import Event as Stamp
from lem.records.base import Moment

if TYPE_CHECKING:
    from lem.adapters.forge_gh_shell import Gh

QUERY = """query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number url title body state author { login }
      headRefOid headRefName baseRefName mergeable mergeCommit { oid }
      autoMergeRequest { enabledAt }
      mergeQueueEntry { __typename id createdAt: enqueuedAt head: headCommit { oid } }
      timelineItems(last: 2, itemTypes: [
        ADDED_TO_MERGE_QUEUE_EVENT, REMOVED_FROM_MERGE_QUEUE_EVENT,
        AUTO_MERGE_ENABLED_EVENT, AUTO_MERGE_DISABLED_EVENT
      ]) {
        nodes {
          __typename
          ... on AddedToMergeQueueEvent { id createdAt }
          ... on RemovedFromMergeQueueEvent { id createdAt reason head: beforeCommit { oid } }
          ... on AutoMergeEnabledEvent { id createdAt }
          ... on AutoMergeDisabledEvent { id createdAt reason }
        }
      }
    }
  }
}"""


ADDED = "AddedToMergeQueueEvent"
REMOVED = "RemovedFromMergeQueueEvent"
ENABLED = "AutoMergeEnabledEvent"
DISABLED = "AutoMergeDisabledEvent"
PAIR = 2


class Oid(msgspec.Struct, frozen=True):
    """A commit as GitHub names it."""

    oid: str


class Event(msgspec.Struct, frozen=True):
    """A queue event; only the removal and disable events have a reason."""

    kind: str = msgspec.field(name="__typename")
    id: str | None = None
    at: Moment | None = msgspec.field(name="createdAt", default=None)
    reason: str | None = None
    head: Oid | None = None

    def stamp(self) -> Stamp | None:
        """The identity and time GitHub supplies, when both are present."""
        if self.id and self.at is not None:
            head = self.head.oid if self.head else None
            return Stamp(id=self.id, at=self.at, head=head)
        return None


class Timeline(msgspec.Struct, frozen=True):
    """The latest event of the kinds the query names."""

    nodes: tuple[Event | None, ...] | None

    def latest(self) -> Event | None:
        """The last item of the timeline."""
        return self.nodes[-1] if self.nodes else None


def viewed(gh: Gh, number: int) -> str:
    """Read the request and its queue evidence in the same GitHub call."""
    owner, repo = gh.named().split("/", 1)
    return gh.said(
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
        "--jq",
        ".data.repository.pullRequest",
    )


def removed(event: Event | None) -> str | None:
    """GitHub's removal and its reason when GitHub gives one."""
    if event is None:
        return None
    if event.kind == REMOVED:
        return event.reason or "GitHub removed the pull request from the merge queue"
    if event.kind == DISABLED:
        return event.reason or "GitHub disabled auto-merge for the pull request"
    return None


def entered(timeline: Timeline | None) -> Stamp | None:
    """The entry before a removal, if the two events are from the same queue."""
    nodes = timeline.nodes if timeline else None
    if nodes is None or len(nodes) < PAIR:
        return None
    first, last = nodes[-2:]
    if first is None or last is None:
        return None
    if (first.kind, last.kind) in {(ADDED, REMOVED), (ENABLED, DISABLED)}:
        return first.stamp()
    return None


def evidence(
    event: Event | None, queued: str | None, entry: Event | None
) -> Stamp | None:
    """Use the live entry or the latest event that describes the request's queue state."""
    if entry is not None:
        return entry.stamp() if entry.head else None
    if event is None or (queued == "auto-merge" and event.kind != ENABLED):
        return None
    return event.stamp()

"""GitHub's latest queue event and the entry it still holds, read together."""

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from lem.adapters.forge_gh_shell import Gh

QUERY = """query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number url title body state author { login }
      headRefOid headRefName baseRefName mergeable mergeCommit { oid }
      autoMergeRequest { enabledAt }
      mergeQueueEntry { id }
      timelineItems(last: 1, itemTypes: [
        ADDED_TO_MERGE_QUEUE_EVENT, REMOVED_FROM_MERGE_QUEUE_EVENT,
        AUTO_MERGE_ENABLED_EVENT, AUTO_MERGE_DISABLED_EVENT
      ]) {
        nodes {
          __typename
          ... on RemovedFromMergeQueueEvent { reason }
          ... on AutoMergeDisabledEvent { reason }
        }
      }
    }
  }
}"""


class Event(msgspec.Struct, frozen=True):
    """A queue event; only the removal and disable events have a reason."""

    kind: str = msgspec.field(name="__typename")
    reason: str | None = None


class Timeline(msgspec.Struct, frozen=True):
    """The latest event of the kinds the query names."""

    nodes: tuple[Event | None, ...] | None


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


def removed(timeline: Timeline | None) -> str | None:
    """GitHub's reason for removal when the latest event confirms it."""
    if timeline is None:
        return None
    for event in timeline.nodes or ():
        if event and event.kind in {
            "RemovedFromMergeQueueEvent",
            "AutoMergeDisabledEvent",
        }:
            return event.reason
    return None

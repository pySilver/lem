"""The GitHub evidence that survives a merge call and its recovery."""

from datetime import datetime
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

import msgspec

from lem.adapters import forge_gh_queue
from lem.adapters.forge_gh import ForgeGh
from lem.adapters.forge_gh_pulls import Pulls
from lem.adapters.forge_gh_shell import GhPull, Oid
from lem.app.landing import merge_called
from lem.ports.forge_facts import MergeDone, MergeText
from unit.landing.worlds import BASE, BRANCH, MERGE, PULL, SEEN, TIP

if TYPE_CHECKING:
    from pathlib import Path

REPLAYED = "a" * 40
FIRST = "f" * 40


def test_the_same_merge_reread_keeps_the_parent_before_the_replayed_commits() -> None:
    done = MergeDone(commit=MERGE, merged_head=TIP, base_parent=BASE)
    seen = msgspec.structs.replace(
        SEEN, state="merged", merge_commit=MERGE, merged_head=TIP, base_parent=REPLAYED
    )
    kept = merge_called.merged_pull(seen, done)
    assert kept.base_parent == BASE


class QueueForge(ForgeGh):
    """A forge with a removal event from the accepted merge attempt."""

    def said(self, *args: str, given: str | None = None) -> str:
        return msgspec.json.encode(
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "mergeQueueEntry": None,
                            "timelineItems": {
                                "nodes": [
                                    {
                                        "__typename": "RemovedFromMergeQueueEvent",
                                        "createdAt": "2027-01-01T12:01:00Z",
                                        "beforeCommit": {"oid": TIP},
                                        "reason": "a required check failed in the queue",
                                    }
                                ]
                            },
                        }
                    }
                }
            }
        ).decode()

    def named(self) -> str:
        return "o/p"


def test_github_supplies_the_reason_of_a_confirmed_removal(tmp_path: Path) -> None:
    forge = QueueForge(checkout=tmp_path, environ={})
    since = datetime.fromisoformat("2027-01-01T12:00:00Z")
    facts = forge_gh_queue.queue(forge, PULL.number, TIP, since)
    assert facts.dequeued == "a required check failed in the queue"
    later = datetime.fromisoformat("2027-01-01T12:02:00Z")
    assert forge_gh_queue.queue(forge, PULL.number, TIP, later).dequeued is None
    assert forge_gh_queue.queue(forge, PULL.number, REPLAYED, since).dequeued is None


class RebaseForge(Pulls):
    """The forge reports a merge commit, and a rebase of two commits."""

    def tried(self, *args: str, given: str | None = None) -> CompletedProcess[str]:
        return CompletedProcess(args, 0)

    def said(self, *args: str, given: str | None = None) -> str:
        if args[0] == "api":
            if "--paginate" in args:
                return msgspec.json.encode(
                    [[commit(FIRST, BASE, "first"), commit(TIP, FIRST, "last")]]
                ).decode()
            sha = args[1].rsplit("/", 1)[-1]
            parent, message = {
                MERGE: (REPLAYED, "last"),
                REPLAYED: (BASE, "first"),
                TIP: (FIRST, "last"),
            }[sha]
            return msgspec.json.encode(commit(sha, parent, message)).decode()
        return msgspec.json.encode(
            GhPull(
                number=PULL.number,
                url=PULL.url,
                title=PULL.title,
                body="",
                state="MERGED",
                head_ref_oid=TIP,
                head_ref_name=BRANCH,
                base_ref_name="main",
                merge_commit=Oid(MERGE),
            )
        ).decode()

    def named(self) -> str:
        return "o/p"

    def commits(self, number: int) -> int:
        return 2

    def parent(self, commit: str, depth: int = 1) -> str:
        assert commit == MERGE
        return {1: REPLAYED, 2: BASE}[depth]


def commit(sha: str, parent: str, message: str) -> dict[str, object]:
    return {
        "sha": sha,
        "parents": [{"sha": parent}],
        "commit": {
            "author": {
                "name": "Dev",
                "email": "dev@example.com",
                "date": "2027-01-01T12:00:00Z",
            },
            "message": message,
        },
    }


def test_the_forge_recovery_read_accepts_verified_rebase_depth(tmp_path: Path) -> None:
    forge = RebaseForge(checkout=tmp_path, environ={})
    done = forge.merge(PULL.number, TIP, "rebase", MergeText(subject="", body=""))
    assert isinstance(done, MergeDone)
    assert done.base_parent == BASE
    recovered = forge.pull(PULL.number)
    assert recovered.base_parent == BASE


def test_confirmed_queue_removal_reaches_reconciliation_even_with_auto_merge(
    tmp_path: Path,
) -> None:
    from unittest.mock import Mock

    from lem.app.landing import merge_world, pull_identity
    from lem.model.landing import reconcile
    from lem.ports.forge_facts import Pull
    from lem.records.landing.merge import MergeAccepted, Refused
    from unit.landing.merges import facing, opened

    since = datetime.fromisoformat("2027-01-01T12:00:00Z")
    forge = QueueForge(checkout=tmp_path, environ={})
    record = opened(accepted=MergeAccepted(tip=TIP, at=since, queued="the merge queue"))
    pull = Pull(
        number=PULL.number,
        url=PULL.url,
        title=PULL.title,
        state="open",
        head=TIP,
        head_ref=BRANCH,
        base="main",
        queued="auto-merge",
    )
    world = pull_identity.observed(forge, record, facing(), pull)
    context = Mock(world=world, record=record, ports=Mock(forge=forge))
    confirmed = reconcile.queued(
        record, world, dequeued=merge_world.dequeued_of(context)
    )
    assert isinstance(confirmed, Refused)
    assert (confirmed.kind, confirmed.source, confirmed.line) == (
        "rule",
        "github",
        "a required check failed in the queue",
    )

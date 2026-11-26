"""The GitHub evidence that survives a merge call and its recovery."""

import shlex
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess

import msgspec
import pytest

from fakes.repo import RealRepo, git_env, run_git
from lem.adapters.forge_gh import ForgeGh
from lem.adapters.forge_gh_pulls import Pulls
from lem.adapters.forge_gh_queue import Oid
from lem.adapters.forge_gh_shell import Gh, GhPull
from lem.app.landing import merge_reply, pull_identity
from lem.kernel.errors import Refusal
from lem.model.landing import queue_evidence, reconcile_queue
from lem.ports.forge_facts import MergeDone, MergeText
from lem.records.landing.merge import MergeAccepted, Refused
from unit.landing.merges import facing, opened
from unit.landing.worlds import BASE, BRANCH, MERGE, PULL, SEEN, TIP

REPLAYED = "a" * 40
FIRST = "f" * 40


def test_the_same_merge_reread_keeps_the_parent_before_the_replayed_commits() -> None:
    done = MergeDone(commit=MERGE, merged_head=TIP, base_parent=BASE)
    seen = msgspec.structs.replace(
        SEEN, state="merged", merge_commit=MERGE, merged_head=TIP, base_parent=REPLAYED
    )
    from unittest.mock import Mock

    from lem.ports.forge_facts import Pull

    shown = Pull(
        number=seen.number,
        url=seen.url,
        title=seen.title,
        state="merged",
        head=TIP,
        head_ref=BRANCH,
        base="main",
        merge_commit=MERGE,
        merged_head=TIP,
        base_parent=REPLAYED,
    )
    context = Mock(record=opened())
    context.ports.forge.pull.return_value = shown
    kept = merge_reply.merged_pull(context, seen.number, done)
    assert kept.base_parent == BASE


class QueueForge(ForgeGh):
    """A forge with a removal event from the accepted merge attempt."""

    def said(self, *args: str, given: str | None = None) -> str:
        return msgspec.json.encode(
            {
                "number": PULL.number,
                "url": PULL.url,
                "title": PULL.title,
                "body": "",
                "state": "OPEN",
                "headRefOid": TIP,
                "headRefName": BRANCH,
                "baseRefName": "main",
                "autoMergeRequest": {"enabledAt": "2027-01-01T12:00:00Z"},
                "timelineItems": {
                    "nodes": [
                        {
                            "__typename": "RemovedFromMergeQueueEvent",
                            "id": "removed",
                            "createdAt": "2027-01-01T12:01:00Z",
                            "head": {"oid": TIP},
                            "reason": "a required check failed in the queue",
                        }
                    ]
                },
            }
        ).decode()

    def named(self) -> str:
        return "o/p"


def test_github_supplies_the_reason_of_a_confirmed_removal(tmp_path: Path) -> None:
    forge = QueueForge(checkout=tmp_path, environ={})
    since = datetime.fromisoformat("2027-01-01T12:00:00Z")
    pull = pull_identity.seen(forge.pull(PULL.number))
    call = MergeAccepted(tip=TIP, at=since, queued="the merge queue")
    assert queue_evidence.matched(pull, call)
    assert pull.dequeued == "a required check failed in the queue"
    later = datetime.fromisoformat("2027-01-01T12:02:00Z")
    assert not queue_evidence.matched(pull, msgspec.structs.replace(call, at=later))
    assert not queue_evidence.matched(pull, msgspec.structs.replace(call, tip=REPLAYED))


class RebaseForge(Pulls):
    """The forge reports a merge commit, and a rebase of two commits."""

    def tried(self, *args: str, given: str | None = None) -> CompletedProcess[str]:
        return CompletedProcess(args, 0)

    def said(self, *args: str, given: str | None = None) -> str:
        if args[0] == "api" and args[1] != "graphql":
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
    since = datetime.fromisoformat("2027-01-01T12:00:00Z")
    forge = QueueForge(checkout=tmp_path, environ={})
    record = opened(accepted=MergeAccepted(tip=TIP, at=since, queued="the merge queue"))
    world = pull_identity.in_world(forge, record, facing())
    confirmed = reconcile_queue.queued(record, world)
    assert isinstance(confirmed, Refused)
    assert (confirmed.kind, confirmed.source, confirmed.line) == (
        "rule",
        "github",
        "a required check failed in the queue",
    )


def test_the_command_that_points_origin_at_github_keeps_a_path_with_a_space(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "a workspace" / "repo", {"README.md": b"hello\n"})
    run_git(repo.checkout, "remote", "set-url", "origin", "https://gitlab.com/o/r.git")
    gh = Gh(checkout=repo.checkout, environ=git_env())
    with pytest.raises(Refusal) as refused:
        gh.named()
    git, where, *words = shlex.split(refused.value.fix.split("(", 1)[1].split(")")[0])
    assert (git, where, Path(words[0]).resolve()) == (
        "git",
        "-C",
        repo.checkout.resolve(),
    )
    run_git(Path(words[0]), *words[1:4], "git@github.com:owner/repo.git")
    assert gh.named() == "owner/repo"

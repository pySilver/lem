"""How the `gh` adapter runs `gh`: one process for each call, in the main checkout (which tells
`gh` the repository), with the environment of the call, and its JSON read into typed structs.

A call that must succeed raises `Unanswered` with gh's last words; one whose exit the caller
reads goes through `tried`.
"""

import subprocess
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.ports.faults import Unanswered
from lem.ports.forge_facts import Mergeable, Pull

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

type PullState = Literal["open", "closed", "merged"]

GH = "gh"
# The longest a call to GitHub may take before it counts as no answer, in seconds
# (unmeasured estimate).
TIMEOUT = 120
FIELDS = (
    "number,url,title,body,state,headRefOid,headRefName,baseRefName,mergeable,"
    "mergeCommit,autoMergeRequest"
)
STATES: Mapping[str, PullState] = MappingProxyType(
    {
        "OPEN": "open",
        "CLOSED": "closed",
        "MERGED": "merged",
    }
)
MERGEABLE: Mapping[str, Mergeable] = MappingProxyType(
    {
        "MERGEABLE": "mergeable",
        "CONFLICTING": "conflicting",
        "UNKNOWN": "unknown",
    }
)


class Oid(msgspec.Struct, frozen=True):
    """A commit as `gh` names it."""

    oid: str


class GhPull(msgspec.Struct, frozen=True, rename="camel"):
    """A pull request as `gh pr view --json FIELDS` prints it."""

    number: int
    url: str
    title: str
    body: str
    state: Literal["OPEN", "CLOSED", "MERGED"]
    head_ref_oid: str
    head_ref_name: str
    base_ref_name: str
    mergeable: Literal["MERGEABLE", "CONFLICTING", "UNKNOWN"] = "UNKNOWN"
    merge_commit: Oid | None = None
    auto_merge_request: dict[str, object] | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class Gh:
    """The main checkout `gh` runs in, and the environment of the call."""

    checkout: Path
    environ: Mapping[str, str]

    def tried(self, *args: str) -> subprocess.CompletedProcess[str]:
        """`gh ARGS` in the main checkout, whatever its exit code."""
        try:
            return subprocess.run(
                [GH, *args],
                cwd=self.checkout,
                capture_output=True,
                text=True,
                env=dict(self.environ),
                stdin=subprocess.DEVNULL,
                timeout=TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Unanswered(GH, str(error)) from error

    def said(self, *args: str) -> str:
        """The output of `gh ARGS`; a failure is `Unanswered` with gh's last words."""
        ran = self.tried(*args)
        if ran.returncode:
            raise Unanswered(GH, last_words(ran))
        return ran.stdout

    def parent(self, commit: str) -> str:
        """The first parent of `commit` on the forge: the base a squash or a merge went onto."""
        repo = self.said(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        )
        path = f"repos/{repo.strip()}/commits/{commit}"
        return self.said("api", path, "--jq", ".parents[0].sha").strip()

    def pull_of(self, found: GhPull) -> Pull:
        """A pull request as the port gives it; a merged one with its merge's base."""
        merged = found.merge_commit.oid if found.merge_commit else None
        done = found.state == "MERGED" and merged is not None
        return Pull(
            number=found.number,
            url=found.url,
            title=found.title,
            body=found.body,
            state=STATES[found.state],
            head=found.head_ref_oid,
            head_ref=found.head_ref_name,
            base=found.base_ref_name,
            mergeable=MERGEABLE[found.mergeable],
            queued="auto-merge" if found.auto_merge_request else None,
            merge_commit=merged,
            merged_head=found.head_ref_oid if done else None,
            base_parent=self.parent(merged) if done and merged else None,
        )


def last_words(ran: subprocess.CompletedProcess[str]) -> str:
    """What gh said last: the last line of its errors, else of its output, else its code."""
    lines = (ran.stderr or ran.stdout).strip().splitlines()
    return lines[-1].strip() if lines else f"gh exited {ran.returncode}"

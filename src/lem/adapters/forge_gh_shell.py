"""How the `gh` adapter runs `gh`: one process for each call, in the main checkout (which tells
`gh` the repository), with the environment of the call, and its JSON read into typed structs.

A call that must succeed raises `Unanswered` with gh's last words; one whose exit the caller
reads goes through `tried`. A `gh` that is not on the PATH, or not logged in, is a refusal that
names the fix, never an empty answer: no pull request is "none" because `gh` could not ask.
"""

import re
import subprocess
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import msgspec

from lem.adapters import forge_gh_origin, forge_gh_queue
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import Mergeable, Pull

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

type PullState = Literal["open", "closed", "merged"]

GH = "gh"
PR = "pr"
JSON = "--json"
UTF8 = "utf-8"
# What in a caller's environment would aim gh or git at another repository than the checkout's.
AIMED = frozenset(
    ("GH_REPO", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
)
GITHUB = re.compile(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$")
# What gh says when it has no login for the host (`gh auth login`), in any of its forms.
NO_LOGIN = re.compile(
    r"gh auth login|not logged in|authentication required", re.IGNORECASE
)
# The longest a call to GitHub may take before it counts as no answer, in seconds
# (unmeasured estimate; a first `gh pr create` took 8 to 12 seconds, trial-skeleton,
# 2026-11-25).
TIMEOUT = 120
FIELDS = (
    "number,url,title,body,state,author,headRefOid,headRefName,baseRefName,mergeable,"
    "mergeCommit,autoMergeRequest"
)
STATES: Mapping[str, PullState] = MappingProxyType(
    {"OPEN": "open", "CLOSED": "closed", "MERGED": "merged"}
)
MERGEABLE: Mapping[str, Mergeable] = MappingProxyType(
    {"MERGEABLE": "mergeable", "CONFLICTING": "conflicting", "UNKNOWN": "unknown"}
)


class Login(msgspec.Struct, frozen=True):
    """A person as `gh` names one."""

    login: str


class GhPull(msgspec.Struct, frozen=True, rename="camel"):
    """A pull request as GitHub gives it, with queue evidence on a direct read."""

    number: int
    url: str
    title: str
    body: str
    state: Literal["OPEN", "CLOSED", "MERGED"]
    head_ref_oid: str
    head_ref_name: str
    base_ref_name: str
    author: Login | None = None
    mergeable: Literal["MERGEABLE", "CONFLICTING", "UNKNOWN"] = "UNKNOWN"
    merge_commit: forge_gh_queue.Oid | None = None
    auto_merge_request: dict[str, object] | None = None
    merge_queue_entry: forge_gh_queue.Event | None = None
    timeline_items: forge_gh_queue.Timeline | None = None

    def queued(self) -> str | None:
        """The queue that still holds the request."""
        if self.merge_queue_entry is not None:
            return "the merge queue"
        last = self.timeline_items.latest() if self.timeline_items else None
        if last is not None and last.kind == forge_gh_queue.REMOVED:
            return None
        return None if self.auto_merge_request is None else "auto-merge"


def cleaned(environ: Mapping[str, str]) -> dict[str, str]:
    """The environment of a call, but what would send `gh` or git to another repository."""
    return {name: word for name, word in environ.items() if name not in AIMED}


def last_words(ran: subprocess.CompletedProcess[str]) -> str:
    """What gh said last: the last line of its errors, else of its output, else its code."""
    lines = (ran.stderr or ran.stdout).strip().splitlines()
    return lines[-1].strip() if lines else f"gh exited {ran.returncode}"


def unanswered(ran: subprocess.CompletedProcess[str]) -> Refusal | Unanswered:
    """A failed call as what it says: no login is a refusal with its fix; anything else is
    gh's last words."""
    if NO_LOGIN.search(f"{ran.stderr}\n{ran.stdout}"):
        return Refusal(
            "gh-login",
            "gh has no login for GitHub in this environment (it looks under "
            "XDG_CONFIG_HOME, or GH_TOKEN)",
            "run gh auth login in the shell the step runs in, then run the step again",
        )
    return Unanswered(GH, last_words(ran))


@dataclass(frozen=True, kw_only=True, slots=True)
class Gh:
    """The main checkout `gh` runs in, and the environment of the call."""

    checkout: Path
    environ: Mapping[str, str]

    def tried(
        self, *args: str, given: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        """`gh ARGS` in the main checkout, whatever its exit code, with `given` on its
        standard input; a call of `gh pr` names the repository of the configured origin,
        whatever `GH_REPO` says."""
        named = ("--repo", self.named()) if args[0] == PR else ()
        try:
            return subprocess.run(
                [GH, *args, *named],
                cwd=self.checkout,
                capture_output=True,
                text=True,
                env=cleaned(self.environ),
                input=given or "",
                timeout=TIMEOUT,
                check=False,
            )
        except FileNotFoundError as error:
            raise Refusal(
                "no-gh",
                "the remote is GitHub and the gh command is not on the PATH",
                "install gh and sign in (gh auth login), then run the step again",
            ) from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Unanswered(GH, str(error)) from error

    def said(self, *args: str, given: str | None = None) -> str:
        """The output of `gh ARGS`; a failure is `Unanswered` with gh's last words, or the
        refusal of a gh with no login."""
        ran = self.tried(*args, given=given)
        if ran.returncode:
            raise unanswered(ran)
        return ran.stdout

    def named(self) -> str:
        """`OWNER/NAME` of the configured origin on GitHub, as its URL names it."""
        ran = subprocess.run(
            ["git", "-C", str(self.checkout), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            env=cleaned(self.environ),
            check=False,
        )
        found = GITHUB.search(ran.stdout.strip())
        if found is None:
            raise forge_gh_origin.not_github(self.checkout)
        return found[1]

    def parent(self, commit: str, depth: int = 1) -> str:
        """The commit `depth` first parents before `commit` on the forge: the base a squash
        or a merge went onto (1), or the one before the first commit a rebase replayed."""
        found = commit
        for _ in range(depth):
            path = f"repos/{self.named()}/commits/{found}"
            found = self.said("api", path, "--jq", ".parents[0].sha").strip()
        return found

    def viewed(self, number: int, depth: int = 1) -> Pull:
        """The pull request `number` as the forge shows it now; `depth` is how many commits
        a rebase merge of it replayed."""
        return self.pull_of(packet(self, number), depth)

    def commits(self, number: int) -> int:
        """How many commits the pull request holds, GitHub's own total (REST `commits` of a
        pull request): a rebase replays each. `gh pr view --json commits` lists at most 100
        (gh 2.101.0 asks for `commits(first: 100)`, the review of 2026-11-25)."""
        path = f"repos/{self.named()}/pulls/{number}"
        return int(self.said("api", path, "--jq", ".commits").strip() or "1")

    def pull_of(self, found: GhPull, depth: int | None = 1) -> Pull:
        """A pull request as the port gives it; a merged one with its merge's base."""
        merged = found.merge_commit.oid if found.merge_commit else None
        done = found.state == "MERGED" and merged is not None
        queued = found.queued()
        open_unqueued = found.state == "OPEN" and queued is None
        latest = found.timeline_items.latest() if found.timeline_items else None
        return Pull(
            number=found.number,
            url=found.url,
            title=found.title,
            body=found.body,
            state=STATES[found.state],
            author=found.author.login if found.author else None,
            head=found.head_ref_oid,
            head_ref=found.head_ref_name,
            base=found.base_ref_name,
            mergeable=MERGEABLE[found.mergeable],
            queued=queued,
            dequeued=forge_gh_queue.removed(latest) if open_unqueued else None,
            queue_event=forge_gh_queue.evidence(
                latest, queued, found.merge_queue_entry
            ),
            queue_entered=forge_gh_queue.entered(found.timeline_items)
            if open_unqueued
            else None,
            merge_commit=merged,
            merged_head=found.head_ref_oid if done else None,
            base_parent=self.parent(merged, depth)
            if done and merged and depth is not None
            else None,
        )


def packet(gh: Gh, number: int) -> GhPull:
    """The typed JSON returned by gh for the pull request."""
    said = forge_gh_queue.viewed(gh, number)
    return msgspec.json.decode(said, type=GhPull)

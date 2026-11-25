"""The pull requests of the `Forge` port through `gh` (`ForgePulls`), and the delete of a branch's
copy with a lease (`ForgeRefs`).

A merge pins the head it names (`--match-head-commit`), and its answer is read back from the
forge: merged, taken by a queue, or refused in GitHub's words. The copy of a branch is deleted by
a push with a lease on the commit named, so a push that came in between stops it.
"""

import subprocess
from typing import TYPE_CHECKING

import msgspec

from lem.adapters.forge_gh_shell import FIELDS, Gh, GhPull, cleaned, last_words
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import MergeDenied, MergeDone, MergeTaken, Repo

if TYPE_CHECKING:
    from lem.ports.forge_facts import MergeMethod, MergeOutcome, MergeText, Pull

JSON = "--json"
PR = "pr"
METHODS = ("squash", "merge")
# What only GitHub's own answer to a merge says: its API's refusal, in its words.
GITHUBS = (
    "graphql:",
    "head branch was modified",
    "not mergeable",
    "merge conflict",
    "protected branch",
    "required status",
    "review is required",
)


class Pulls(Gh):
    """The pull requests, and the merge."""

    def repo(self) -> Repo:
        said = self.said("repo", "view", self.named(), JSON, "nameWithOwner,url")
        found = msgspec.json.decode(said)
        return Repo(name=found["nameWithOwner"], url=found["url"])

    def find_pulls(self, head: str, base: str | None) -> tuple[Pull, ...]:
        chosen = ("--base", base) if base else ()
        said = self.said(
            PR, "list", "--head", head, *chosen, "--state", "all", JSON, FIELDS
        )
        found = msgspec.json.decode(said, type=list[GhPull])
        return tuple(self.pull_of(pull) for pull in found if pull.head_ref_name == head)

    def open_pull(self, head: str, base: str, title: str, body: str) -> Pull:
        made = self.said(
            PR,
            "create",
            "--head",
            head,
            "--base",
            base,
            "--title",
            title,
            "--body",
            body,
        )
        address = made.strip().splitlines()[-1].rstrip("/")
        return self.pull(int(address.rsplit("/", 1)[-1]))

    def update_pull(self, number: int, title: str, body: str) -> Pull:
        self.said(PR, "edit", str(number), "--title", title, "--body", body)
        return self.pull(number)

    def pull(self, number: int) -> Pull:
        said = self.said(PR, "view", str(number), JSON, FIELDS)
        return self.pull_of(msgspec.json.decode(said, type=GhPull))

    def open_pulls(self) -> tuple[Pull, ...]:
        said = self.said(PR, "list", "--state", "open", "--limit", "100", JSON, FIELDS)
        return tuple(
            self.pull_of(pull) for pull in msgspec.json.decode(said, type=list[GhPull])
        )

    def merge(
        self, number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> MergeOutcome:
        if method not in METHODS:
            raise Refusal(
                "not-built",
                f"a {method} merge through gh is not built yet",
                "the step `land-merge` builds it (docs/plans/2026-11-25-lem-built-again.md)",
            )
        pinned = ("--match-head-commit", expected_head, f"--{method}")
        words = ("--subject", text.subject, "--body", text.body)
        ran = self.tried(PR, "merge", str(number), *pinned, *words)
        found = self.pull(number)
        if ran.returncode and found.state != "merged":
            return denied(ran)
        if found.merge_commit and found.merged_head and found.base_parent:
            return MergeDone(
                commit=found.merge_commit,
                merged_head=found.merged_head,
                base_parent=found.base_parent,
            )
        return MergeTaken(
            queued=found.queued or "GitHub took the merge and has not merged"
        )


class Refs(Gh):
    """The forge's copy of a task branch, deleted only at the commit named."""

    def delete_ref(self, name: str, expect: str) -> bool:
        lease = f"--force-with-lease={name}:{expect}"
        ran = subprocess.run(
            [
                "git",
                "-C",
                str(self.checkout),
                "push",
                "--quiet",
                lease,
                "origin",
                f":{name}",
            ],
            capture_output=True,
            text=True,
            env=cleaned(self.environ),
            stdin=subprocess.DEVNULL,
            check=False,
        )
        return not ran.returncode


def denied(ran: subprocess.CompletedProcess[str]) -> MergeDenied:
    """GitHub's refusal of a merge, by its words: a head that moved, a base that cannot take
    it, or a rule of the base branch. Words that are not GitHub's own answer (a lost
    connection, a timeout) say nothing of the merge: they are `Unanswered`, and the intent
    stays for the reconcile (`landing.md` E, "Stop or lost reply around the merge call")."""
    said = last_words(ran)
    lowered = said.lower()
    if not any(mark in lowered for mark in GITHUBS):
        raise Unanswered("gh", said)
    if "head" in lowered and "modified" in lowered:
        return MergeDenied(kind="tip", said=said)
    if "conflict" in lowered:
        return MergeDenied(kind="base", said=said)
    return MergeDenied(kind="rule", said=said)

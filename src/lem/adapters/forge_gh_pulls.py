"""The pull requests of the `Forge` port through `gh` (`ForgePulls`), and the delete of a branch's
copy with a lease (`ForgeRefs`).

A text goes to `gh` on its standard input (`--body-file -`), never as an argument, whatever its
length. A merge pins the head it names (`--match-head-commit`), and its answer is read back from
the forge: merged, taken by a queue, or refused in GitHub's words; a rebase merge's base is the
commit before the first one it replayed. The copy of a branch is deleted by a push with a lease
on the commit named, so a push that came in between stops it.
"""

import subprocess
from typing import TYPE_CHECKING

import msgspec
from msgspec.structs import replace

from lem.adapters import forge_gh_history
from lem.adapters.forge_gh_shell import (
    FIELDS,
    JSON,
    PR,
    Gh,
    GhPull,
    cleaned,
    last_words,
    packet,
)
from lem.ports.faults import Unanswered
from lem.ports.forge_facts import MergeDenied, MergeDone, MergeTaken, Repo

if TYPE_CHECKING:
    from lem.ports.forge import Forge
    from lem.ports.forge_facts import MergeMethod, MergeOutcome, MergeText, Pull

BODY = ("--body-file", "-")
# How many open pull requests into one branch `pulls_into` reads; that many is a fault, so that
# none is missed. A guess: a feature's branch takes a few parts at a time.
INTO_LIMIT = 500
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
            *BODY,
            given=body,
        )
        return self.pull(number_of(made))

    def update_pull(self, number: int, title: str | None, body: str) -> Pull:
        named = () if title is None else ("--title", title)
        words = (*named, *BODY)
        self.said(PR, "edit", str(number), *words, given=body)
        return self.pull(number)

    def pull(self, number: int) -> Pull:
        read = packet(self, number)
        shown = self.pull_of(read, depth=None)
        if shown.state != "merged" or shown.merge_commit is None:
            return shown
        parent = forge_gh_history.parent(self, read, shown.merge_commit)
        return replace(shown, base_parent=parent)

    def open_pulls(self) -> tuple[Pull, ...]:
        said = self.said(PR, "list", "--state", "open", "--limit", "100", JSON, FIELDS)
        return tuple(
            self.pull_of(pull) for pull in msgspec.json.decode(said, type=list[GhPull])
        )

    def merge(
        self, number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> MergeOutcome:
        pinned = ("--match-head-commit", expected_head, f"--{method}")
        replayed = self.commits(number) if method == "rebase" else 1
        words = (*pinned, "--subject", text.subject, *BODY)
        called = (PR, "merge", str(number), *words)
        ran = self.tried(*called, given=text.body)
        return outcome(ran, self.viewed(number, replayed))


class Refs(Gh):
    """The forge's copy of a task branch, deleted only at the commit named, and the open pull
    requests into a branch."""

    def pulls_into(self, branch: str) -> tuple[Pull, ...]:
        words = ("--base", branch, "--state", "open", "--limit", str(INTO_LIMIT))
        said = self.said(PR, "list", *words, JSON, FIELDS)
        found = msgspec.json.decode(said, type=list[GhPull])
        if len(found) >= INTO_LIMIT:
            why = f"{branch} has {INTO_LIMIT} open pull requests or more into it"
            raise Unanswered("gh", f"{why}: Lem reads them all or none")
        return tuple(self.pull_of(pull) for pull in found)

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


def number_of(made: str) -> int:
    """The number of the pull request whose address `gh pr create` printed last."""
    lines = made.strip().splitlines() or [""]
    address = lines[-1].rstrip("/")
    number = address.rsplit("/", 1)[-1]
    if not number.isdigit():
        raise Unanswered(
            "gh", f"gh pr create printed no pull request address: {made!r}"
        )
    return int(number)


def outcome(ran: subprocess.CompletedProcess[str], found: Pull) -> MergeOutcome:
    """What a merge call did, from the pull request as the forge shows it after it."""
    if ran.returncode and found.state != "merged":
        return denied(ran)
    if found.merge_commit and found.merged_head and found.base_parent:
        return MergeDone(
            commit=found.merge_commit,
            merged_head=found.merged_head,
            base_parent=found.base_parent,
        )
    return MergeTaken(queued=found.queued or "GitHub took the merge and has not merged")


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


def after_merge(forge: Forge, number: int, done: MergeDone) -> Pull:
    """Read the destination and use the call's evidence when GitHub shows the same merge."""
    if isinstance(forge, Pulls):
        pull = forge.pull_of(packet(forge, number), depth=None)
        same = (pull.merge_commit, pull.merged_head) == (done.commit, done.merged_head)
        if pull.state != "merged" or same:
            return pull
    return forge.pull(number)

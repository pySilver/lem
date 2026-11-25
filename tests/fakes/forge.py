"""`LocalForge`: the `Forge` port over a remote a test holds, `ModelGit` or a `RealRepo`, for
the model level, the journeys and the contract suite (`tests/contract/suites/forge.py`).

It merges the way GitHub does (a squash or a merge commit onto the base, pinned to the head
named), and a test sets what GitHub would do besides: a merge that waits in a queue
(`queue`), a rule that refuses (`refuse`), a merge another hand made (`outside_merge`), a
retarget (`retarget`), a closed pull request (`close`), a pull request GitHub calls conflicting
(`conflicting`), a report that lags behind a merge (`lag`), and an edit of the text that fails
(`fail_edits`). `merge_calls` counts every merge call, as trial R5 does.
"""

from dataclasses import dataclass, field
from typing import Protocol

from msgspec.structs import replace

from lem.ports.faults import Unanswered
from lem.ports.forge_facts import (
    MergeDenied,
    MergeDone,
    MergeMethod,
    MergeOutcome,
    MergeTaken,
    MergeText,
    Pull,
    Repo,
)
from lem.ports.git_facts import Conflict


class Remote(Protocol):
    """What the forge merges through: the remote's branches."""

    def head_of(self, branch: str) -> str | None: ...
    def merge_into(
        self, base: str, head: str, *, squash: bool, message: str
    ) -> str | Conflict: ...
    def delete_remote(self, branch: str, expect: str) -> bool: ...


@dataclass
class LocalForge:
    """Pull requests over `remote`, with what GitHub would do set by the test."""

    remote: Remote
    name: str = "owner/project"
    pulls: dict[int, Pull] = field(default_factory=dict)
    bodies: dict[int, str] = field(default_factory=dict)
    merge_calls: list[tuple[int, str]] = field(default_factory=list)
    queue: bool = False
    refuse: str | None = None
    fail_edits: bool = False
    lag: int = 0
    lagging: dict[int, tuple[Pull, int]] = field(default_factory=dict)
    waiting: dict[int, tuple[str, MergeMethod, MergeText]] = field(default_factory=dict)

    def url(self, number: int) -> str:
        """The address of the pull request `number`."""
        return f"https://github.com/{self.name}/pull/{number}"

    def fresh(self, pull: Pull) -> Pull:
        """An open pull request's head follows its branch on the remote."""
        if pull.state != "open":
            return pull
        head = self.remote.head_of(pull.head_ref)
        return replace(pull, head=head) if head else pull

    # ---- the port ----

    def repo(self) -> Repo:
        return Repo(name=self.name, url=f"https://github.com/{self.name}")

    def find_pulls(self, head: str, base: str | None) -> tuple[Pull, ...]:
        return tuple(
            self.fresh(pull)
            for pull in self.pulls.values()
            if pull.head_ref == head and base in {None, pull.base}
        )

    def open_pull(self, head: str, base: str, title: str, body: str) -> Pull:
        sha = self.remote.head_of(head)
        if sha is None:
            raise Unanswered("gh", f"no branch {head} on the remote")
        if any(p.state == "open" and p.head_ref == head for p in self.pulls.values()):
            raise Unanswered("gh", f"a pull request for branch {head} already exists")
        number = len(self.pulls) + 1
        pull = Pull(
            number=number,
            url=self.url(number),
            title=title,
            state="open",
            head=sha,
            head_ref=head,
            base=base,
            mergeable="mergeable",
        )
        self.pulls[number] = pull
        self.bodies[number] = body
        return pull

    def update_pull(self, number: int, title: str, body: str) -> Pull:
        if self.fail_edits:
            raise Unanswered("gh", "HTTP 502: the edit of the pull request failed")
        self.pulls[number] = replace(self.pulls[number], title=title)
        self.bodies[number] = body
        return self.pull(number)

    def pull(self, number: int) -> Pull:
        if number not in self.pulls:
            raise Unanswered("gh", f"no pull request {number}")
        if number in self.lagging:
            shown, left = self.lagging[number]
            if left > 0:
                self.lagging[number] = (shown, left - 1)
                return shown
            del self.lagging[number]
        return self.fresh(self.pulls[number])

    def open_pulls(self) -> tuple[Pull, ...]:
        return tuple(self.fresh(p) for p in self.pulls.values() if p.state == "open")

    def merge(
        self, number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> MergeOutcome:
        self.merge_calls.append((number, expected_head))
        pull = self.pull(number)
        if pull.state != "open":
            return MergeDenied(kind="rule", said=f"the pull request is {pull.state}")
        if pull.head != expected_head:
            return MergeDenied(kind="tip", said="Head branch was modified")
        if self.refuse is not None:
            return MergeDenied(kind="rule", said=self.refuse)
        if self.queue:
            self.waiting[number] = (expected_head, method, text)
            self.pulls[number] = replace(pull, queued="the merge queue")
            return MergeTaken(queued="the merge queue")
        return self.merged(number, method, text)

    def delete_ref(self, name: str, expect: str) -> bool:
        if not name.startswith("refs/heads/"):
            raise Unanswered("gh", f"{name} is no full name of a branch")
        return self.remote.delete_remote(name.removeprefix("refs/heads/"), expect)

    # ---- what GitHub does besides ----

    def merged(self, number: int, method: MergeMethod, text: MergeText) -> MergeOutcome:
        """Merge the pull request now."""
        pull = self.fresh(self.pulls[number])
        message = f"{text.subject} (#{number})\n\n{text.body}"
        made = self.remote.merge_into(
            pull.base, pull.head, squash=method == "squash", message=message
        )
        if isinstance(made, Conflict):
            self.pulls[number] = replace(pull, mergeable="conflicting")
            return MergeDenied(kind="base", said="the merge has conflicts")
        self.lagging[number] = (pull, self.lag)
        self.pulls[number] = replace(
            pull, state="merged", queued=None, merge_commit=made, merged_head=pull.head
        )
        return MergeDone(commit=made, merged_head=pull.head)

    def settle(self, number: int) -> MergeOutcome:
        """The queue reaches the pull request: it merges."""
        _head, method, text = self.waiting.pop(number)
        return self.merged(number, method, text)

    def outside_merge(self, number: int) -> MergeOutcome:
        """Someone merges the pull request on GitHub."""
        return self.merged(
            number, "squash", MergeText(subject="merged on GitHub", body="")
        )

    def retarget(self, number: int, base: str) -> None:
        """Someone changes the base of the pull request."""
        self.pulls[number] = replace(self.pulls[number], base=base)

    def close(self, number: int) -> None:
        """Someone closes the pull request without a merge."""
        self.pulls[number] = replace(self.pulls[number], state="closed", queued=None)

    def conflicting(self, number: int) -> None:
        """GitHub calls the pull request conflicting at its head."""
        self.pulls[number] = replace(self.pulls[number], mergeable="conflicting")

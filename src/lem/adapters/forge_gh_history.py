"""Find the first parent outside the commits that GitHub replayed."""

from typing import TYPE_CHECKING

import msgspec

from lem.ports.faults import Unanswered

if TYPE_CHECKING:
    from lem.adapters.forge_gh_shell import Gh, GhPull


type Pages = tuple[tuple[Commit, ...], ...]


class Author(msgspec.Struct, frozen=True):
    """The commit's original Git author, whose identity and date a rebase keeps."""

    name: str
    email: str
    date: str


class Message(msgspec.Struct, frozen=True):
    """The part of a Git commit that GitHub preserves when it replays it."""

    author: Author
    message: str


class Commit(msgspec.Struct, frozen=True):
    """A commit and its parents as the GitHub REST API returns them."""

    sha: str
    commit: Message
    parents: tuple[dict[str, str], ...]


def found(gh: Gh, sha: str) -> Commit:
    """The forge's commit at a specific ID."""
    said = gh.said("api", f"repos/{gh.named()}/commits/{sha}")
    return msgspec.json.decode(said, type=Commit)


def originals(gh: Gh, pull: GhPull) -> tuple[Commit, ...]:
    """The PR's original commits, including all pages before the API's list limit."""
    path = f"repos/{gh.named()}/pulls/{pull.number}/commits?per_page=100"
    said = gh.said("api", path, "--paginate", "--slurp")
    pages = msgspec.json.decode(said, type=Pages.__value__)
    listed = tuple(commit for page in pages for commit in page)
    head = listed[-1].sha if listed else None
    if head != pull.head_ref_oid:
        raise Unanswered(
            "gh", "GitHub returned an incomplete list of the pull request's commits"
        )
    if len(listed) != gh.commits(pull.number):
        raise Unanswered("gh", "GitHub did not list every commit of the pull request")
    return listed


def replayed(gh: Gh, merged: Commit, before: tuple[Commit, ...]) -> str | None:
    """Prove the replay by matching the originals in order on a linear first-parent chain."""
    current = merged
    for original in reversed(before):
        if current.commit != original.commit or len(current.parents) != 1:
            return None
        parent = current.parents[0]["sha"]
        if original is before[0]:
            return parent
        current = found(gh, parent)
    return None


def parent(gh: Gh, pull: GhPull, sha: str) -> str:
    """The base parent after a recovery read, from the commits the forge actually wrote."""
    merged = found(gh, sha)
    if not merged.parents:
        raise Unanswered("gh", "GitHub did not report a parent for the merge commit")
    first = merged.parents[0]["sha"]
    if len(merged.parents) != 1:
        return first
    head = found(gh, pull.head_ref_oid)
    if merged.commit != head.commit:
        return first
    return replayed(gh, merged, originals(gh, pull)) or first

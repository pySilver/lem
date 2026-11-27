"""What the `Git` port gives back besides a sha: a conflict, a refusal, a commit, a diff's
size, and a rebase in progress."""

from lem.records.base import Frozen, Sha

# The first words of a push that its lease refused: origin's branch is not at the commit named.
LEASE = "stale info"


class Conflict(Frozen, frozen=True, kw_only=True):
    """A merge or a rebase stopped on these files."""

    files: tuple[str, ...]


class GitRefused(Frozen, frozen=True, kw_only=True):
    """Git refused an act (a hook, a lock, a lease, a branch not at the commit named): its
    words, which begin with LEASE for a push its lease refused."""

    said: str


class Commit(Frozen, frozen=True, kw_only=True):
    """A commit: its sha, its parents, its subject, its author's name, and the id of its
    patch."""

    sha: Sha
    parents: tuple[Sha, ...]
    subject: str
    author: str | None = None
    patch_id: str | None = None


class DiffStat(Frozen, frozen=True, kw_only=True):
    """What changed between two commits: the paths, and the lines added and removed."""

    paths: tuple[str, ...]
    added: int
    removed: int


class RebaseState(Frozen, frozen=True, kw_only=True):
    """A rebase in progress in a worktree: onto what, and the files it stopped on."""

    onto: Sha
    files: tuple[str, ...] = ()

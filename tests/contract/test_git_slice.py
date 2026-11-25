"""The `git` adapter (`lem.adapters.git_cli`) against the `Git` port's contract, on a real
repository: the slice that `slice-land` built for the plain path, which `land-base` takes over
with `tests/contract/test_git.py`."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contract.suites.git import FILES, GitContract
from fakes.repo import RealRepo, git_env, run_git, write
from lem.adapters import git_cli
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class RealWorld:
    """A real repository with its origin, its main checkout and a folder for worktrees."""

    git: git_cli.GitCli
    repo: RealRepo
    worktrees: Path

    @property
    def checkout(self) -> Path:
        return self.repo.checkout

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str:
        return self.repo.outside_commit(branch, files, start)

    def merge_in(self, where: Path, ref: str, files: dict[str, bytes]) -> str:
        run_git(where, "merge", "--quiet", "--no-ff", "--no-commit", ref)
        write(where, dict(files))
        run_git(where, "add", "--all")
        run_git(where, "commit", "--quiet", "--message", f"Merge {ref}")
        return run_git(where, "rev-parse", "HEAD")


def real_world(folder: Path) -> RealWorld:
    """A repository of `FILES` on `main`, pushed and fetched, and git with the test's
    environment."""
    repo = RealRepo.init(folder, dict(FILES))
    place = Place(checkout=repo.checkout, home=folder / "home", environ=git_env())
    return RealWorld(git=git_cli.bind(place), repo=repo, worktrees=folder / "worktrees")


class TestGitCli(GitContract):
    def world(self, folder: Path) -> RealWorld:
        return real_world(folder)

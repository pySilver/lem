"""`ModelGit` against the `Git` port's contract."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contract.suites.git import FILES, GitContract
from fakes.git import ModelGit

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ModelWorld:
    """A `ModelGit` repository, with its checkout and worktrees under one folder."""

    git: ModelGit
    checkout: Path
    worktrees: Path

    def outside_commit(
        self, branch: str, files: dict[str, bytes | None], start: str = "main"
    ) -> str:
        return self.git.outside_commit(branch, files, start)

    def merge_in(self, where: Path, ref: str, files: dict[str, bytes]) -> str:
        return self.git.merge_in(where, ref, files)

    def refuse_commits(self, said: str) -> None:
        self.git.refused_commit = said


class TestModelGit(GitContract):
    def world(self, folder: Path) -> ModelWorld:
        checkout = folder / "checkout"
        return ModelWorld(
            git=ModelGit.init(checkout, dict(FILES)),
            checkout=checkout,
            worktrees=folder / "worktrees",
        )

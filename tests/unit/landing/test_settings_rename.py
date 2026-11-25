"""A settings rename reaches both careful decisions with its literal paths."""

from typing import TYPE_CHECKING

from fakes.repo import RealRepo, git_env, run_git
from lem.adapters.git_cli import GitCli
from lem.app.landing import propose_seen, review_edits
from lem.model.landing import careful, propose_careful
from lem.model.landing.propose_facts import Facts

if TYPE_CHECKING:
    from pathlib import Path


def test_a_settings_rename_keeps_both_paths_and_gits_line_counts(
    tmp_path: Path,
) -> None:
    team = careful.SETTINGS_FILE
    renamed = ".lem/old.toml"
    unusual = "a\tb\nc.txt"
    repo = RealRepo.init(tmp_path, {team: b'[checks]\ncommands = ["true"]\n'})
    checkout = repo.checkout
    base = run_git(checkout, "rev-parse", "HEAD")
    run_git(checkout, "config", "diff.renames", "true")
    run_git(checkout, "mv", team, renamed)
    (checkout / unusual).write_text("one line\n", encoding="utf-8")
    run_git(checkout, "add", "--all")
    run_git(checkout, "commit", "--quiet", "--message", "move settings")
    tip = run_git(checkout, "rev-parse", "HEAD")

    git = GitCli(environ=git_env())
    stats = git.diff_stat(checkout, base, tip)
    assert set(stats.paths) == {team, renamed, unusual}
    assert (stats.added, stats.removed) == (1, 0)
    edits = review_edits.edits(git, checkout, (base, tip), stats.paths)
    assert edits.settings.touched and edits.settings.tip is None
    settings = propose_seen.settings_of(git, checkout, (base, tip))
    reasons = propose_careful.edits(Facts(changed=stats.paths, settings=settings))
    assert len(reasons) == 1 and reasons[0].startswith(f"the change removes {team},")

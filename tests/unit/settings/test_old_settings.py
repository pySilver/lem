"""The onboarding imports a repository's old settings once and leaves valid settings."""

import tomllib
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.repo import run_git
from unit.settings.given import refusal_of
from unit.settings.test_init import repository

if TYPE_CHECKING:
    from pathlib import Path

OLD = ".lem/project.toml"
CURRENT = ".lem/settings.toml"
# The tables and keys of lem-scratch, with distinct values to catch default substitution.
SCRATCH = b"""\
[paths]
plans = 'notes/plans'
[branch]
base = 'stable'
land = 'owner'
history = 'keep'
protected = ['release']
[checks]
commands = ['python3 -m unittest discover -s tests -q']
[flow]
topics = ["a rule changes without the owner's review"]
[seats]
reviewer = 'codex/gpt-6.2-astra:high'
planner = 'claude/opus:low'
experts = ['claude/fable:high', 'codex/gpt-6.2-astra:high']
[corrections]
collect = true
"""


def test_init_imports_the_scratch_keys_and_replaces_the_tracked_old_file(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path, head=False)
    old = repo.checkout / OLD
    old.parent.mkdir()
    old.write_bytes(SCRATCH)
    run_git(repo.checkout, "add", "--", OLD)
    run_git(repo.checkout, "commit", "-m", "test: write the old settings")

    ran = lem("init", "--codex", "no", cwd=repo.checkout)

    assert ran.code == 0, ran.stdout + ran.stderr
    written = tomllib.loads((repo.checkout / CURRENT).read_text())
    expected = tomllib.loads(SCRATCH.decode())
    expected.pop("corrections")
    imported = sorted(
        f"{table}.{key}" for table, entries in expected.items() for key in entries
    )
    for table, entries in expected.items():
        assert {key: written[table][key] for key in entries} == entries
    assert "corrections" not in written
    result = ran.result()
    assert isinstance(result, dict)
    assert result["base"] == "stable"
    assert result["reviewer"] == expected["seats"]["reviewer"]
    assert result["migration"]["imported"] == imported
    assert result["migration"]["dropped"] == ["corrections.collect"]
    assert not old.exists()
    run_git(repo.checkout, "add", "-A", "--", OLD, CURRENT)
    changes = run_git(
        repo.checkout, "diff", "--cached", "--name-status", "--no-renames"
    )
    assert changes.splitlines() == [f"D\t{OLD}", f"A\t{CURRENT}"]


def test_init_keeps_current_values_and_comments_when_both_files_exist(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    old = repo.checkout / OLD
    old.parent.mkdir()
    old.write_text(
        '[branch]\nbase = "old"\n\n[tracker]\nkind = "linear"\nunused = true\n'
    )
    current = repo.checkout / CURRENT
    current.write_text('[branch]\nbase = "mine" # the owner\n')

    ran = lem("init", cwd=repo.checkout)

    assert ran.code == 0, ran.stdout + ran.stderr
    assert 'base = "mine" # the owner' in current.read_text()
    assert tomllib.loads(current.read_text())["tracker"] == {"kind": "linear"}
    result = ran.result()
    assert isinstance(result, dict)
    assert result["migration"]["kept"] == ["branch.base"]
    assert result["migration"]["dropped"] == ["tracker.unused"]
    assert not old.exists()


def test_an_explicit_base_replaces_the_old_default(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    old = repo.checkout / OLD
    old.parent.mkdir()
    old.write_text('[branch]\nbase = "old"\n')

    ran = lem("init", "--base", "chosen", cwd=repo.checkout)

    assert ran.code == 0, ran.stdout + ran.stderr
    assert (
        tomllib.loads((repo.checkout / CURRENT).read_text())["branch"]["base"]
        == "chosen"
    )


@pytest.mark.parametrize("body", [b"[broken\n", b"[checks]\ncommands = true\n"])
def test_a_bad_old_file_stays_when_init_refuses_it(tmp_path: Path, body: bytes) -> None:
    repo = repository(tmp_path)
    old = repo.checkout / OLD
    old.parent.mkdir()
    old.write_bytes(body)

    ran = lem("init", cwd=repo.checkout)

    assert ran.code == 1, ran.stdout + ran.stderr
    assert OLD in refusal_of(ran)["why"]
    assert old.read_bytes() == body
    assert not (repo.checkout / CURRENT).exists()

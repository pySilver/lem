"""`lem settings set`: one line written into the local, home or machine file, checked before
the file changes, every other line and comment kept, and the value then in force with its
`from`; nothing writes the team's file."""

import threading
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.repo import RealRepo, run_git
from lem.kernel.errors import Refusal
from lem.settings import edit, reading
from lem.settings.places import LOCAL, Scope
from lem.settings.write import Asked, set_setting
from unit.settings.given import Given, given

if TYPE_CHECKING:
    from pathlib import Path

    from lem.settings.answer import Set

HOME = "~/config/lem/settings.toml"
MACHINE = "~/config/lem/machine.toml"


def set_in(setup: Given, key: str, word: str, scope: Scope) -> Set:
    """`lem settings set KEY WORD --SCOPE` in the checkout of `setup`."""
    asked = Asked(
        key=key, word=word, scope=scope, folder=setup.checkout, environ=setup.environ
    )
    return set_setting(asked)


def test_set_local_writes_a_whole_seat_and_says_where_it_comes_from(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path, team="[seats]\nreviewer = 'claude/opus:high'\n")
    said = set_in(setup, "seats.reviewer", "codex/gpt-6.2-sol:high", Scope.local)
    assert said.line == 'reviewer = "codex/gpt-6.2-sol:high"'
    assert said.in_force == "codex/gpt-6.2-sol:high"
    assert said.source == ".lem/settings.local.toml"
    assert 'reviewer = "codex/gpt-6.2-sol:high"' in (setup.checkout / LOCAL).read_text()


def test_set_home_under_a_nearer_file_says_the_nearer_one_comes_first(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path, team="[seats]\nmerger = 'codex:high'\n")
    said = set_in(setup, "seats.merger", "claude:low", Scope.home)
    assert said.source == ".lem/settings.toml"
    assert said.said.endswith(f"which comes before {HOME}")
    assert (setup.home / "settings.toml").read_text().count("merger") == 1


@pytest.mark.parametrize(
    ("key", "word", "said"),
    [
        ("seats.reviewer", "codex/gpt:high:low", "holds 2 `:`"),
        ("seats.reviewer", "codex", "names no model and no effort"),
        ("seats.reviewer", "gemini/pro:high", "names the agent 'gemini'"),
        ("seats.reviewer", "false", "Expected `str`"),
        ("seats.planner", "codex/gpt-6.2-sol:high", "must be claude"),
        ("seats.experts", "claude/a:b,codex/c:d,claude/e:f", "length <= 2"),
        ("seats.reviwer", "codex/a:b", "did you mean reviewer?"),
        ("seats", "codex/a:b", "names no setting"),
    ],
)
def test_set_refuses_a_value_its_key_does_not_take_and_writes_nothing(
    tmp_path: Path, key: str, word: str, said: str
) -> None:
    setup = given(tmp_path, local="# the owner's own note\n[seats]\nmerger = 'codex'\n")
    before = (setup.checkout / LOCAL).read_text()
    with pytest.raises(Refusal) as caught:
        set_in(setup, key, word, Scope.local)
    assert said in f"{caught.value.why} {caught.value.fix}"
    assert (setup.checkout / LOCAL).read_text() == before


def test_default_takes_the_line_out_and_keeps_every_other_line_as_written(
    tmp_path: Path,
) -> None:
    text = (
        "# the owner's own note\n[seats]\n# who reviews here\n"
        "reviewer = 'codex/a:high'  # for a while\nmerger   =   'codex'\n"
    )
    setup = given(tmp_path, team="[seats]\nreviewer = 'claude/opus:high'\n", local=text)
    said = set_in(setup, "seats.reviewer", "default", Scope.local)
    assert said.line is None
    assert said.source == ".lem/settings.toml"
    assert said.said.endswith(".lem/settings.local.toml names none")
    assert (setup.checkout / LOCAL).read_text() == (
        "# the owner's own note\n[seats]\n# who reviews here\nmerger   =   'codex'\n"
    )


def test_a_file_left_with_nothing_but_lems_line_goes(tmp_path: Path) -> None:
    setup = given(tmp_path)
    set_in(setup, "seats.reviewer", "codex/a:high", Scope.local)
    assert (setup.checkout / LOCAL).read_text().startswith("# This machine's own")
    set_in(setup, "seats.reviewer", "default", Scope.local)
    assert not (setup.checkout / LOCAL).exists()


def test_the_experts_are_written_as_a_list_and_false_turns_the_fallback_off(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path)
    experts = set_in(
        setup, "seats.experts", "claude/fable:high, codex/x:high", Scope.home
    )
    assert experts.in_force == ("claude/fable:high", "codex/x:high")
    assert experts.line == 'experts = ["claude/fable:high","codex/x:high"]'
    fallback = set_in(setup, "seats.fallback", "false", Scope.home)
    assert fallback.in_force is False


@pytest.mark.parametrize(
    ("key", "word", "written"),
    [
        ("load.start", "none", 0),
        ("load.start", "12.5", 12.5),
        ("handoff.tokens", "0", 0),
        ("handoff.tokens", "200000", 200000),
        ("corrections.collect", "yes", True),
        ("corrections.collect", "no", False),
        ("serve.port", "5101", 5101),
        ("serve.tailscale", "on", True),
        ("peers.studio", "4537", 4537),
    ],
)
def test_set_machine_writes_the_machines_numbers_and_switches(
    tmp_path: Path, key: str, word: str, written: object
) -> None:
    said = set_in(given(tmp_path), key, word, Scope.machine)
    assert said.in_force == written
    assert said.source == MACHINE


def test_default_gives_the_machines_number_back_to_lem(tmp_path: Path) -> None:
    setup = given(tmp_path, machine="[handoff]\ntokens = 200000\n[load]\nstart = 9\n")
    said = set_in(setup, "handoff.tokens", "default", Scope.machine)
    assert said.in_force == 600_000
    assert said.source == "Lem's default"
    assert (setup.home / "machine.toml").read_text() == "[load]\nstart = 9\n"


@pytest.mark.parametrize(
    ("key", "word", "scope", "fix"),
    [
        ("checks.commands", "make", Scope.local, "edit .lem/settings.toml by hand"),
        ("corrections.collect", "yes", Scope.local, "--machine"),
        ("seats.reviewer", "codex/a:b", Scope.machine, "--home or --local"),
        ("state.keep_days", "3", Scope.home, "--local"),
        ("ask.style", "bold", Scope.local, "--home"),
    ],
)
def test_a_table_its_file_may_not_hold_is_refused_with_the_file_that_may(
    tmp_path: Path, key: str, word: str, scope: Scope, fix: str
) -> None:
    with pytest.raises(Refusal) as caught:
        set_in(given(tmp_path), key, word, scope)
    assert caught.value.code == "table-place"
    assert fix in caught.value.fix


def test_a_wrong_value_already_in_the_file_is_refused_and_the_file_stays(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path, machine="# mine\n[handoff]\ntokens = 5\n")
    with pytest.raises(Refusal, match="is under 100000"):
        set_in(setup, "load.start", "9", Scope.machine)
    assert (
        setup.home / "machine.toml"
    ).read_text() == "# mine\n[handoff]\ntokens = 5\n"


def test_a_handoff_under_the_floor_is_refused_and_writes_nothing(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path)
    with pytest.raises(Refusal, match="is under 100000"):
        set_in(setup, "handoff.tokens", "50000", Scope.machine)
    assert not (setup.home / "machine.toml").exists()


@pytest.mark.parametrize(
    "machine",
    [
        "serve.port = 4536\n",
        "[serve]\nport = 4536 # the board\n",
        "serve = { port = 4536 }\n",
        "[serve]\n'port' = 4536\n",
    ],
)
def test_a_table_in_another_form_keeps_its_form_and_the_new_key(
    tmp_path: Path, machine: str
) -> None:
    setup = given(tmp_path, machine=machine)
    set_in(setup, "serve.tailscale", "yes", Scope.machine)
    text = (setup.home / "machine.toml").read_text()
    assert "4536" in text
    assert "tailscale" in text
    found = set_in(setup, "serve.tailscale_port", "4600", Scope.machine)
    assert found.in_force == 4600


def test_two_writers_at_once_each_keep_the_others_line(tmp_path: Path) -> None:
    setup = given(tmp_path)
    where = reading.Where(checkout=None, home=setup.home, environ=setup.environ)
    path = setup.home / "machine.toml"
    setup.home.mkdir(parents=True, exist_ok=True)
    edits = [
        edit.Edit(
            scope=Scope.machine,
            path=path,
            lock=setup.home / "machine.lock",
            table="peers",
            key=f"host{number}",
            given=4000 + number,
        )
        for number in range(8)
    ]
    threads = [
        threading.Thread(target=edit.applied, args=(one, where)) for one in edits
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert path.read_text().count("host") == 8


def test_set_local_from_a_tasks_worktree_writes_the_main_checkouts_file(
    tmp_path: Path,
) -> None:
    team = b"[branch]\nbase = 'main'\n"
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": team})
    worktree = repo.checkout / ".lem" / "worktrees" / "fix-it"
    run_git(repo.checkout, "worktree", "add", "--quiet", "-b", "fix-it", str(worktree))
    ran = lem(
        "settings",
        "set",
        "seats.reviewer",
        "codex/gpt-6.2-sol:high",
        "--local",
        cwd=worktree,
    )
    assert ran.code == 0, ran.stderr
    assert (repo.checkout / LOCAL).is_file()
    assert not (worktree / LOCAL).exists()
    shown = lem("settings", "show", cwd=worktree).result()
    assert isinstance(shown, dict)
    assert shown["settings"]["seats"]["reviewer"] == "codex/gpt-6.2-sol:high"
    assert shown["from"]["seats.reviewer"] == ".lem/settings.local.toml"
    assert shown["seats"]["reviewer"]["agent"] == "codex"

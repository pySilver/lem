"""The four files read and checked: each table in its place, each key known, each value of its
form, and every value in force from the nearest file that holds it, with its `from`."""

from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.repo import RealRepo, run_git
from lem.kernel.errors import Refusal
from lem.settings import described, load
from lem.settings.team import Team
from unit.settings.given import given

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT = "Lem's default"
TEAM = ".lem/settings.toml"
LOCAL = ".lem/settings.local.toml"
HOME = "~/config/lem/settings.toml"
MACHINE = "~/config/lem/machine.toml"


def refused(root: Path, **files: str) -> Refusal:
    """The refusal of the settings the case writes."""
    with pytest.raises(Refusal) as caught:
        given(root, **files).loaded()
    return caught.value


def test_with_no_file_every_value_is_lems_default(tmp_path: Path) -> None:
    found = given(tmp_path).loaded()
    assert found.settings.branch.land == "agent"
    assert found.settings.branch.history == "squash"
    assert found.settings.state.keep_days == 30
    assert found.settings.naps.on is False
    assert found.settings.jev.findings is True
    assert found.settings.paths.plans == "docs/plans"
    assert found.settings.paths.plan_file == "YYYY-MM-DD-<slug>.md"
    assert found.settings.paths.rulings == "docs/rulings.md"
    assert found.settings.seats.reviewer == "claude/opus:high"
    assert found.settings.seats.fallback == "claude/opus:high"
    assert found.settings.seats.experts == (
        "claude/fable:high",
        "codex/gpt-6.2-astra:high",
    )
    assert found.settings.load.start == 40
    assert found.settings.handoff.tokens == 600_000
    assert found.settings.corrections.collect is False
    assert found.settings.tracker is None
    assert set(found.sources.values()) == {DEFAULT}


def test_the_teams_file_holds_21_keys() -> None:
    tables = [field.name for field in msgspec.structs.fields(Team)]
    assert sum(len(described.keys_of(Team, table)) for table in tables) == 21


@pytest.mark.parametrize(
    ("files", "code", "said"),
    [
        ({"team": "[tools]\nwebrev = true\n"}, "settings-key", "[tools] is no table"),
        ({"team": "[branch]\nbse = 'main'\n"}, "settings-key", "did you mean base?"),
        (
            {"team": "[paths]\nruling_file = 'x.md'\n"},
            "settings-key",
            "valid: plans, plan_file, rulings",
        ),
        ({"team": "[flow]\ntopic = []\n"}, "settings-key", "did you mean topics?"),
        (
            {"team": "[tracker]\nkind = 'github'\nteam = 'x'\n"},
            "settings-key",
            "tracker.team",
        ),
        (
            {"local": "[checks]\ncommands = []\n"},
            "table-place",
            f"move [checks] to {TEAM}",
        ),
        ({"local": "[corrections]\ncollect = true\n"}, "table-place", MACHINE),
        ({"machine": "[seats]\nreviewer = 'x'\n"}, "table-place", HOME),
        ({"home": "[state]\nkeep_days = 3\n"}, "table-place", f"{TEAM} or {LOCAL}"),
        ({"team": "[load]\nstart = 3\n"}, "table-place", MACHINE),
        ({"team": "[ask]\nstyle = 'bold'\n"}, "table-place", HOME),
        ({"team": "[branch\n"}, "settings-toml", "is not TOML"),
    ],
    ids=lambda value: str(value)[:40],
)
def test_a_table_or_key_out_of_place_is_refused_with_the_place_or_the_nearest(
    tmp_path: Path, files: dict[str, str], code: str, said: str
) -> None:
    found = refused(tmp_path, **files)
    assert found.code == code
    assert said in f"{found.why} {found.fix}"


def test_a_file_that_is_not_utf8_is_refused_by_name(tmp_path: Path) -> None:
    setup = given(tmp_path)
    (setup.checkout / LOCAL).write_bytes(b"[naps]\non = false # \xff\n")
    with pytest.raises(Refusal) as caught:
        setup.loaded()
    assert "is not UTF-8" in caught.value.why
    assert LOCAL in caught.value.why


@pytest.mark.parametrize(
    ("team", "fix"),
    [
        ("[branch]\nland = 'robot'\n", '"agent" or "owner"'),
        ("[branch]\nhistory = 'rebase'\n", '"squash" or "keep"'),
        ("[branch]\nbase = ''\n", "branch.base"),
        ("[checks]\ncommands = 'make test'\n", "checks.commands"),
        ("[checks]\ncommands = ['make', ' ']\n", "checks.commands"),
        ("[checks]\nsetup = ['']\n", "checks.setup"),
        ("[flow]\ntopics = 'money'\n", "flow.topics"),
        ("[state]\nkeep_days = 0\n", "state.keep_days"),
        ("[state]\nkeep_days = true\n", "state.keep_days"),
        ("[state]\nkeep_days = 1.5\n", "state.keep_days"),
        ("[tracker]\nkind = 'jira'\n", "tracker.kind"),
        ("[tracker]\n", "tracker.kind"),
        ("[jev]\nfindings = 'no'\n", "jev.findings"),
        ("[naps]\non = 'yes'\n", "naps.on"),
    ],
)
def test_a_wrong_value_is_refused_with_what_its_key_takes(
    tmp_path: Path, team: str, fix: str
) -> None:
    found = refused(tmp_path, team=team)
    assert found.code == "settings"
    assert fix in found.fix
    assert TEAM in found.why


@pytest.mark.parametrize(
    ("team", "said"),
    [
        ("[branch]\nbase = 'main'\nprotected = ['main']\n", "no task could land"),
        ("[paths]\nplans = '/tmp/plans'\n", "is absolute"),
        ("[paths]\nplans = '../elsewhere'\n", "leaves the checkout"),
        ("[paths]\nplans = '.'\n", "is its root"),
        ("[paths]\nrulings = 'docs/rulings'\n", "no markdown file"),
        ("[paths]\nplan_file = 'YYYY-MM-DD.md'\n", "<slug> not once"),
        ("[paths]\nplan_file = 'plans/<slug>.md'\n", "holds a folder"),
        ("[paths]\nplan_file = '<slug>.txt'\n", "does not end with .md"),
        ("[paths]\nplan_file = '<slug>-<day>.md'\n", "a token Lem does not know"),
        ("[paths]\nplan_file = 'YYYY-YYYY-<slug>.md'\n", "holds YYYY twice"),
    ],
)
def test_a_value_its_type_takes_and_a_rule_does_not_is_refused(
    tmp_path: Path, team: str, said: str
) -> None:
    found = refused(tmp_path, team=team)
    assert said in found.why


def test_the_rulings_file_may_not_be_a_folder(tmp_path: Path) -> None:
    setup = given(tmp_path, team="[paths]\nrulings = 'docs/rulings.md'\n")
    (setup.checkout / "docs" / "rulings.md").mkdir(parents=True)
    with pytest.raises(Refusal, match="no markdown file"):
        setup.loaded()


@pytest.mark.parametrize(
    ("line", "said"),
    [
        ("reviewer = 'codex'", "names no model and no effort"),
        ("reviewer = 'codex/gpt-6.2-sol'", "names no effort"),
        ("planner = 'codex/gpt-6.2-sol:high'", "must be claude"),
        ("reviewer = 'codex/gpt:high:low'", "holds 2 `:`"),
        ("reviewer = 'codex/gpt high'", "holds a space"),
        ("reviewer = 'gemini/pro:high'", "names the agent 'gemini'"),
        ("merger = 'claude/:high'", "an empty model"),
        ("session = 'codex:high'", "must be claude"),
        ("experts = ['claude/fable']", "names no effort"),
        ("fallback = 'claude'", "names no model and no effort"),
    ],
)
def test_a_seat_that_does_not_read_by_its_rule_is_refused(
    tmp_path: Path, line: str, said: str
) -> None:
    found = refused(tmp_path, team=f"[seats]\n{line}\n")
    assert said in found.why
    assert "agent/model:effort" in found.fix


@pytest.mark.parametrize(
    ("line", "fix"),
    [
        (
            "experts = ['claude/a:b', 'codex/c:d', 'claude/e:f']",
            "one or two whole seats",
        ),
        ("experts = []", "one or two whole seats"),
        ("fallback = true", "or false"),
        ("reviewer = { agent = 'codex' }", "a whole seat"),
    ],
)
def test_a_seat_of_another_form_is_refused_with_the_seat_form(
    tmp_path: Path, line: str, fix: str
) -> None:
    found = refused(tmp_path, team=f"[seats]\n{line}\n")
    assert fix in found.fix


def test_the_merger_and_the_session_may_leave_out_a_part_and_the_fallback_may_be_off(
    tmp_path: Path,
) -> None:
    team = "[seats]\nmerger = 'codex'\nsession = 'claude:high'\nfallback = false\n"
    found = given(tmp_path, team=team).loaded()
    assert found.settings.seats.merger == "codex"
    assert found.settings.seats.fallback is False


def test_a_wrong_seat_in_a_farther_file_is_refused_too(tmp_path: Path) -> None:
    found = refused(
        tmp_path,
        team="[seats]\nreviewer = 'codex/gpt-6.2-sol:high'\n",
        home="[seats]\nreviewer = 'codex'\n",
    )
    assert HOME in found.why


def test_each_seat_comes_from_the_nearest_file_that_names_it(tmp_path: Path) -> None:
    found = given(
        tmp_path,
        local="[seats]\nreviewer = 'codex/a:high'\n",
        team="[seats]\nreviewer = 'codex/b:high'\nplanner = 'claude/b:high'\n",
        home="[seats]\nreviewer = 'codex/c:high'\nplanner = 'claude/c:high'\n"
        "merger = 'codex:low'\nexperts = ['claude/fable:low']\n",
    ).loaded()
    assert found.settings.seats.reviewer == "codex/a:high"
    assert found.sources["seats.reviewer"] == LOCAL
    assert found.settings.seats.planner == "claude/b:high"
    assert found.sources["seats.planner"] == TEAM
    assert found.settings.seats.merger == "codex:low"
    assert found.sources["seats.merger"] == HOME
    assert found.settings.seats.experts == ("claude/fable:low",)
    assert found.sources["seats.experts"] == HOME
    assert found.sources["seats.session"] == DEFAULT


@pytest.mark.parametrize(("team_days", "local_days"), [(30, 7), (7, 90)])
def test_the_local_files_days_win_lower_or_higher(
    tmp_path: Path, team_days: int, local_days: int
) -> None:
    found = given(
        tmp_path,
        team=f"[state]\nkeep_days = {team_days}\n",
        local=f"[state]\nkeep_days = {local_days}\n",
    ).loaded()
    assert found.settings.state.keep_days == local_days
    assert found.sources["state.keep_days"] == LOCAL


def test_the_local_file_may_say_no_to_the_naps_and_nothing_else(tmp_path: Path) -> None:
    found = given(
        tmp_path, team="[naps]\non = true\n", local="[naps]\non = false\n"
    ).loaded()
    assert found.settings.naps.on is False
    assert found.sources["naps.on"] == LOCAL
    with pytest.raises(Refusal, match=r"naps\.on"):
        given(tmp_path / "yes", local="[naps]\non = true\n").loaded()


def test_the_team_names_the_naps_jev_and_the_tracker(tmp_path: Path) -> None:
    team = "[naps]\non = true\n[jev]\nfindings = false\n[tracker]\nkind = 'github'\n"
    found = given(tmp_path, team=team).loaded()
    assert found.settings.naps.on is True
    assert found.settings.jev.findings is False
    assert found.settings.tracker is not None
    assert found.settings.tracker.kind == "github"
    assert found.sources["jev.findings"] == TEAM
    assert found.sources["tracker.kind"] == TEAM


@pytest.mark.parametrize(
    ("machine", "said"),
    [
        ("[load]\nstart = -1\n", "load.start"),
        ("[handoff]\ntokens = 50000\n", "is under 100000"),
        ("[corrections]\ncollect = 'yes'\n", "corrections.collect"),
        ("[serve]\nport = 70000\n", "serve.port"),
        ("[peers]\nMac = 4537\n", "peers"),
        ("[load]\nstrat = 3\n", "did you mean start?"),
    ],
)
def test_a_wrong_value_of_the_machines_file_is_refused_with_its_fix(
    tmp_path: Path, machine: str, said: str
) -> None:
    found = refused(tmp_path, machine=machine)
    assert said in f"{found.why} {found.fix}"
    assert MACHINE in found.why


def test_the_machines_values_hold_with_their_source(tmp_path: Path) -> None:
    machine = (
        "[load]\nstart = 0\n[handoff]\ntokens = 0\n[corrections]\ncollect = true\n"
        "[peers]\nstudio = 4537\n"
    )
    found = given(tmp_path, machine=machine).loaded()
    assert found.settings.load.start == 0
    assert found.settings.handoff.tokens == 0
    assert found.settings.corrections.collect is True
    assert found.settings.peers == {"studio": 4537}
    assert found.sources["corrections.collect"] == MACHINE
    assert found.sources["peers.studio"] == MACHINE


def test_outside_a_repository_only_the_home_files_are_read(tmp_path: Path) -> None:
    setup = given(tmp_path, home="[ask]\nstyle = 'bold'\n")
    found = load.settings_of(None, setup.environ)
    assert found.settings.ask.style == "bold"
    assert found.sources["ask.style"] == HOME


def test_team_of_reads_the_teams_file_and_base_of_names_the_base(
    tmp_path: Path,
) -> None:
    setup = given(tmp_path, team="[branch]\nbase = 'trunk'\n")
    assert load.base_of(load.team_of(setup.checkout)) == "trunk"
    with pytest.raises(Refusal) as caught:
        load.base_of(load.team_of(given(tmp_path / "none").checkout))
    assert caught.value.code == "no-base"
    with pytest.raises(Refusal) as missing:
        load.team_of(tmp_path / "nowhere")
    assert missing.value.code == "no-settings"


def test_the_main_checkout_on_another_branch_reads_the_bases_commit(
    tmp_path: Path,
) -> None:
    base = b"[branch]\nbase = 'main'\nland = 'agent'\n"
    repo = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": base})
    run_git(repo.checkout, "checkout", "--quiet", "-b", "colleague")
    (repo.checkout / TEAM).write_text("[branch]\nbase = 'main'\nland = 'owner'\n")
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    found = load.settings_of(repo.checkout, environ)
    assert found.settings.branch.land == "agent"
    assert found.sources["branch.land"] == f"main:{TEAM}"
    run_git(repo.checkout, "checkout", "--quiet", "main")
    (repo.checkout / TEAM).write_text("[branch]\nbase = 'main'\nland = 'owner'\n")
    on_base = load.settings_of(repo.checkout, environ)
    assert on_base.settings.branch.land == "owner"
    assert on_base.sources["branch.land"] == TEAM

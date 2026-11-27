"""`lem uninstall` from its entry, on a computer of two repositories, with stand-ins for
`claude` (a script on the PATH that logs each call), the board server, git and cronn's status."""

import json
import os
import shutil
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import httpx
import pytest

from fakes.records import record
from lem import __main__ as entry
from lem.adapters.git_cli import GitCli
from lem.board import look, publish, stopping, tailnet
from lem.board.facts import Stopped
from lem.cli import lazy
from lem.cli.doctor import look as doctor
from lem.cli.doctor import reads
from lem.cli.uninstall.cronn import runs_lem
from lem.kernel import paths
from lem.ports.faults import Unanswered
from lem.store import tasks

if TYPE_CHECKING:
    from lem.records.task import Status

SHELL = "Bash(lem *)"
NIGHT = "JOB_NAME=paper JOB_PROMPT='/lem night' /cronn/jobs/agent-session-job.sh"
RETRO = "cd /work && /opt/homebrew/bin/lem retro"
OTHER = "echo lem"
JOBS_FILE = "# the owner's own note\njobs:\n  - command: whatever\n"
CLAUDE = """#!/bin/sh
printf '%s|%s\\n' "$PWD" "$*" >> "$CLAUDE_LOG"
case "$*" in "$CLAUDE_FAILS") echo "it stays" >&2; exit 1;; esac
"""


def write_json(path: Path, body: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class Machine:
    """The computer: Lem's home, two repositories, Claude Code's files, cronn, and a log of
    each call the stand-ins took."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.home = paths.home(os.environ)
        self.user = Path(os.environ["HOME"])
        self.first = tmp / "paper crane"
        self.second = tmp / "small boat"
        self.pages = tmp / "TMPDIR" / "lem-ask"
        self.claude_log = tmp / "claude.log"
        self.cronn = self.user / ".config" / "cronn"
        self.calls: list[tuple[object, ...]] = []
        self.failing: Path | None = None
        self.stop_said = Stopped(stopped=True, pid=7)
        self.read_rule = reads.read_line(doctor.looked(os.environ, tmp))
        self.others = ["Bash(git status)", "Read(//other/**)"]

    def built(self) -> None:
        for repo in (self.first, self.second):
            (repo / ".lem").mkdir(parents=True)
            (repo / ".lem" / "settings.toml").write_text("# the team's\n")
        write_json(self.home / "workspaces.json", [str(self.first), str(self.second)])
        self.task(self.first, "ended", "landed")
        self.task(self.second, "asked", "answered")
        self.pages.mkdir()
        self.claude_files()
        self.cronn.mkdir(parents=True)
        (self.cronn / "cronn.env").write_text("CRONN_PORT=8123\n")
        (self.cronn / "crontab.yml").write_text(JOBS_FILE)

    def task(self, repo: Path, slug: str, status: Status) -> Path:
        tasks.create(
            repo / ".lem" / "state", record(slug, status=status, branch=f"fix/{slug}")
        )
        tree = repo / ".lem" / "worktrees" / slug
        tree.mkdir(parents=True)
        (tree.parent / ".gitignore").write_text("*\n")
        return tree

    def claude_files(self) -> None:
        installs = [
            {"scope": "user"},
            {"scope": "project", "projectPath": str(self.first)},
            {"scope": "local", "projectPath": str(self.first)},
        ]
        write_json(
            self.user / ".claude" / "plugins" / "installed_plugins.json",
            {"version": 2, "plugins": {"lem@lem": installs, "other@x": installs}},
        )
        allow = {"allow": [SHELL, *self.others, self.read_rule], "deny": [SHELL]}
        lem = {"lem": {"source": {}}, "other": {}}
        write_json(
            self.user / ".claude" / "settings.json",
            {"permissions": allow, "extraKnownMarketplaces": lem, "model": "opus"},
        )
        write_json(
            self.first / ".claude" / "settings.json", {"extraKnownMarketplaces": lem}
        )
        write_json(
            self.first / ".claude" / "settings.local.json",
            {"permissions": allow, "hooks": {"Stop": []}},
        )
        stand_in = self.tmp / "bin" / "claude"
        stand_in.parent.mkdir()
        stand_in.write_text(CLAUDE)
        stand_in.chmod(0o755)

    def claude_calls(self) -> list[tuple[Path, str]]:
        if not self.claude_log.exists():
            return []
        lines = self.claude_log.read_text().splitlines()
        return [
            (Path(cwd).resolve(), words)
            for cwd, words in (one.split("|") for one in lines)
        ]

    def stop(self, _environ: object) -> Stopped:
        assert self.home.is_dir(), "the server stops before the home folder goes"
        self.calls.append(("stop",))
        return self.stop_said

    def worktree_remove(self, checkout: Path, tree: Path) -> None:
        self.calls.append(("remove", checkout, tree))
        if tree == self.failing:
            raise Unanswered("git", f"'{tree}' contains modified or untracked files")
        shutil.rmtree(tree)

    def said(self, checkout: Path, *words: str) -> str:
        assert words == ("worktree", "prune")
        self.calls.append(("prune", checkout))
        return ""

    def status(self, url: str, **given: object) -> httpx.Response:
        assert url == "http://127.0.0.1:8123/api/v1/status"
        assert given["trust_env"] is False
        self.calls.append(("cronn",))
        jobs = [
            {"command": one, "schedule": "0 3 * * *"} for one in (NIGHT, RETRO, OTHER)
        ]
        return httpx.Response(
            200, json={"jobs": jobs}, request=httpx.Request("GET", url)
        )


@pytest.fixture
def machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Machine:
    for name in ("HOME", "XDG_CONFIG_HOME", "TMPDIR"):
        (tmp_path / name).mkdir()
        monkeypatch.setenv(name, str(tmp_path / name))
    monkeypatch.setattr("tempfile.tempdir", None)
    for name in ("CLAUDE_CONFIG_DIR", "CRONN_CONFIG_DIR", "CLAUDE_FAILS"):
        monkeypatch.delenv(name, raising=False)
    stand = Machine(tmp_path.resolve())
    stand.built()
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}:/usr/bin:/bin")
    monkeypatch.setenv("CLAUDE_LOG", str(stand.claude_log))
    monkeypatch.setattr(stopping, "stop", stand.stop)
    monkeypatch.setattr(GitCli, "worktree_remove", stand.worktree_remove)
    monkeypatch.setattr(GitCli, "said", stand.said)
    monkeypatch.setattr(GitCli, "commit_at", lambda _git, _where, ref: ref)
    monkeypatch.setattr(httpx, "get", stand.status)
    return stand


def answered(monkeypatch: pytest.MonkeyPatch, word: str) -> None:
    monkeypatch.setattr(os, "isatty", lambda _fd: True)
    monkeypatch.setattr("sys.stdin", StringIO(f"{word}\n"))


def called(capsys: pytest.CaptureFixture[str], *words: str) -> SimpleNamespace:
    code = lazy.main(["uninstall", *words])
    said = capsys.readouterr()
    return SimpleNamespace(code=code, body=json.loads(said.out), lines=said.err)


def test_it_answers_whatever_the_versions_and_starts_no_board_server() -> None:
    assert "uninstall" in entry.UNCHECKED
    assert not look.wanted("uninstall", {})


def test_with_no_one_at_the_terminal_and_no_yes_it_refuses_before_any_read(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "isatty", lambda _fd: False)
    refused = called(capsys)
    assert refused.code == 1
    assert refused.body["refusal"]["code"] == "uninstall-unattended"
    assert "lem uninstall --yes" in refused.body["refusal"]["fix"]
    assert machine.calls == []
    assert machine.home.is_dir()


def test_yes_removes_lems_parts_in_order_and_keeps_each_repositorys_state(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    ran = called(capsys, "--yes")
    assert ran.code == 0, ran.body
    assert "Remove this?" not in ran.lines
    assert machine.claude_calls() == [
        (machine.user, "plugin uninstall lem@lem --scope user"),
        (machine.first, "plugin uninstall lem@lem --scope project"),
        (machine.first, "plugin uninstall lem@lem --scope local"),
        (machine.user, "plugin marketplace remove lem --scope user"),
        (machine.first, "plugin marketplace remove lem --scope project"),
    ]
    assert machine.calls == [("cronn",), ("stop",)]
    assert not machine.home.exists()
    assert not machine.pages.exists()
    for repo in (machine.first, machine.second):
        assert (repo / ".lem" / "state").is_dir()
        assert (repo / ".lem" / "settings.toml").is_file()
    assert (machine.first / ".lem" / "worktrees" / "ended").is_dir()
    result = ran.body["result"]
    assert f"the branch fix/ended of {machine.first}" in result["kept"]
    committed = f"commit the change of {machine.first / '.claude' / 'settings.json'}"
    assert result["left_for_owner"].count(committed) == 1
    assert result["left_for_owner"][-1] == "brew uninstall pySilver/tap/lem"
    assert ran.lines.splitlines()[-1].endswith("brew uninstall pySilver/tap/lem")


def test_only_lems_two_allow_rules_leave_each_settings_file(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    linked = machine.tmp / "dotfiles" / "settings.json"
    linked.parent.mkdir()
    user = machine.user / ".claude" / "settings.json"
    user.rename(linked)
    user.symlink_to(linked)
    assert called(capsys, "--yes").code == 0
    assert user.is_symlink()
    kept = {"allow": machine.others, "deny": [SHELL]}
    assert read_json(user) == {
        "permissions": kept,
        "extraKnownMarketplaces": {"lem": {"source": {}}, "other": {}},
        "model": "opus",
    }
    assert read_json(machine.first / ".claude" / "settings.local.json") == {
        "permissions": kept,
        "hooks": {"Stop": []},
    }


def test_cronn_jobs_that_run_lem_are_left_for_the_owner_and_the_file_stays_as_it_was(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    ran = called(capsys, "--yes")
    jobs = machine.cronn / "crontab.yml"
    assert jobs.read_text() == JOBS_FILE
    named = [
        line for line in ran.body["result"]["left_for_owner"] if "cronn job" in line
    ]
    assert named == [
        f"delete the cronn job {one!r} (0 3 * * *) from {jobs}; cronn reads that file "
        "again within 10 s"
        for one in (NIGHT, RETRO)
    ]


def test_with_no_cronn_set_up_it_asks_no_status(
    machine: Machine, capsys: pytest.CaptureFixture[str]
) -> None:
    (machine.cronn / "cronn.env").unlink()
    assert called(capsys, "--yes").code == 0
    assert ("cronn",) not in machine.calls


@pytest.mark.parametrize("status", ["queued", "building", "landing"])
def test_an_open_task_refuses_before_any_removal(
    machine: Machine, capsys: pytest.CaptureFixture[str], status: Status
) -> None:
    machine.task(machine.second, "open-one", status)
    refused = called(capsys, "--yes")
    assert refused.code == 1
    assert refused.body["refusal"]["code"] == "uninstall-open-tasks"
    assert f"open-one in {machine.second}" in refused.body["refusal"]["why"]
    assert "--force" in refused.body["refusal"]["fix"]
    assert machine.calls == []
    assert machine.claude_calls() == []
    assert machine.home.is_dir()


def test_all_removes_the_state_and_each_worktree_through_git(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answered(monkeypatch, "all")
    ran = called(capsys)
    assert ran.code == 0, ran.body
    assert ran.lines.count("Remove this?") == 1
    for repo, slug in ((machine.first, "ended"), (machine.second, "asked")):
        assert ("remove", repo, repo / ".lem" / "worktrees" / slug) in machine.calls
        assert ("prune", repo) in machine.calls
        assert not (repo / ".lem" / "state").exists()
        assert not (repo / ".lem" / "worktrees").exists()
        assert (repo / ".lem" / "settings.toml").is_file()


def test_force_keeps_the_open_tasks_worktree_branch_and_state(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened = machine.task(machine.second, "open-one", "building")
    answered(monkeypatch, "all")
    ran = called(capsys, "--force")
    assert ran.code == 0, ran.body
    assert opened.is_dir()
    assert ("remove", machine.second, opened) not in machine.calls
    assert not (machine.second / ".lem" / "worktrees" / "asked").exists()
    assert (machine.second / ".lem" / "state").is_dir()
    assert not (machine.first / ".lem" / "state").exists()
    kept = ran.body["result"]["kept"]
    assert f"the worktree {opened} of the open task open-one" in kept
    assert f"the branch fix/open-one of {machine.second}" in kept


@pytest.mark.parametrize("word", ["no", ""])
def test_no_or_no_answer_removes_nothing(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    word: str,
) -> None:
    answered(monkeypatch, word)
    refused = called(capsys)
    assert refused.body["refusal"]["code"] == "uninstall-no"
    assert machine.calls == [("cronn",)]
    assert machine.claude_calls() == []
    assert machine.home.is_dir()


def test_a_task_opened_while_the_question_waits_refuses(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "isatty", lambda _fd: True)

    def opened_meanwhile(*_words: object, **_given: object) -> str:
        machine.task(machine.first, "new-one", "queued")
        return "all"

    monkeypatch.setattr("click.prompt", opened_meanwhile)
    refused = called(capsys)
    assert refused.body["refusal"]["code"] == "uninstall-changed"
    assert ("stop",) not in machine.calls
    assert (machine.first / ".lem" / "state").is_dir()


def test_a_failed_plugin_removal_keeps_the_marketplace_and_the_home_and_the_rest_runs(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_FAILS", "plugin uninstall lem@lem --scope project")
    ran = called(capsys, "--yes")
    assert ran.code == 1
    assert ran.body["refusal"]["code"] == "uninstall-incomplete"
    assert "it stays" in ran.body["refusal"]["why"]
    assert "lem uninstall again" in ran.body["refusal"]["fix"]
    assert not [one for one in machine.claude_calls() if "marketplace" in one[1]]
    result = ran.body["result"]
    assert (
        f"Lem's allow rules in {machine.user / '.claude' / 'settings.json'}"
        in (result["removed"])
    )
    assert machine.home.is_dir()
    assert not machine.pages.exists()
    assert "brew uninstall pySilver/tap/lem" not in result["left_for_owner"]


def test_a_worktree_git_refuses_keeps_its_repositorys_state_and_the_home(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machine.failing = machine.first / ".lem" / "worktrees" / "ended"
    answered(monkeypatch, "all")
    ran = called(capsys)
    assert ran.code == 1
    assert "modified or untracked" in ran.body["refusal"]["why"]
    assert machine.failing.is_dir()
    assert (machine.first / ".lem" / "state").is_dir()
    assert not (machine.second / ".lem" / "state").exists()
    assert machine.home.is_dir()


def test_a_server_of_another_install_keeps_every_state_and_the_home(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machine.stop_said = Stopped(stopped=False, pid=9, said="another install serves")
    answered(monkeypatch, "all")
    ran = called(capsys)
    assert ran.code == 1
    assert "another install serves" in ran.body["refusal"]["why"]
    assert not [call for call in machine.calls if call[0] == "remove"]
    assert (machine.first / ".lem" / "state").is_dir()
    assert machine.home.is_dir()
    assert len(machine.claude_calls()) == 5


def test_an_open_door_is_closed_before_the_home_folder_goes(
    machine: Machine,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (machine.home / "machine.toml").write_text(
        "[serve]\nport = 45991\ntailscale = true\ntailscale_port = 45992\n"
    )
    monkeypatch.setenv("LEM_TAILSCALE", "/stand-in/tailscale")
    monkeypatch.setattr(
        tailnet, "status", lambda _cli: tailnet.Status(me=tailnet.Me(name="mac.tail."))
    )

    def removed(cli: str, name: str, port: int) -> bool:
        assert machine.home.is_dir()
        machine.calls.append(("door", cli, name, port))
        return True

    monkeypatch.setattr(publish, "removed", removed)
    ran = called(capsys, "--yes")
    assert ran.code == 0, ran.body
    assert ("door", "/stand-in/tailscale", "mac.tail", 45992) in machine.calls
    assert "the tailnet door on port 45992" in ran.body["result"]["removed"]


@pytest.mark.parametrize(
    "command",
    [
        NIGHT,
        RETRO,
        "lem night",
        "exec env PATH=/bin /opt/homebrew/bin/lem retro",
        "/usr/local/bin/claude -p '/lem retro'",
        "true; lem night",
        'A="x y" lem night',
    ],
)
def test_a_job_that_runs_lem(command: str) -> None:
    assert runs_lem(command)


@pytest.mark.parametrize(
    "command",
    [
        OTHER,
        "echo hi # ; lem night",
        "JOB_CWD=/work/lem /cronn/jobs/agent-session-job.sh",
        "claude -p '/lem nightfall'",
        "/opt/homebrew/bin/lemon",
    ],
)
def test_a_job_that_does_not_run_lem(command: str) -> None:
    assert not runs_lem(command)

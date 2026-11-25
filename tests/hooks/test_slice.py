"""Each selector of the plugin's hooks as Claude Code runs it: the line of the installed manifest,
`hooks/hooks.json`, through `hooks/run`, with `LEM_HOOK_BIN` set to this checkout's
`.venv/bin/lem-hook` and the test's own HOME and XDG_CONFIG_HOME (the entry's).

A hook never fails a session: with no app, with bad stdin and with a state folder it cannot write
it says nothing and exits 0. `session-start` appends one framed line that the store reads, and
writes the plugin's folder for the session's commands. A hook imports the standard library only,
and each selector's p95 over 30 runs is at most 55 ms (the design's part 5, part 11 item 5).
"""

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from lem.kernel import folders
from lem.store import sessions

ROOT = Path(__file__).resolve().parents[2]
HOOK = Path(sys.prefix) / "bin" / "lem-hook"
SELECTORS = ("corrections", "serve", "session-start", "precompact", "stop")
SLUG = "fix-the-login"
# The PATH of a Claude Code that a GUI app started (the design's part 5): no `lem` on it.
GUI_PATH = "/usr/bin:/bin"
# The budget of one selector at p95, in milliseconds, and the runs it is read over.
BUDGET = 55.0
RUNS = 30
BAD_INPUTS = (b"", b"not json", b"[1, 2]", b"\xff\xfe\x00", b'{"cwd": 3, "source": 4}')


def manifest_lines() -> dict[str, str]:
    """Each selector's command line, as the installed manifest gives it."""
    manifest = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    commands = (
        hook["command"]
        for groups in manifest["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    )
    return {command.split('hooks/run" ')[1].split()[0]: command for command in commands}


LINES = manifest_lines()


def workspace(folder: Path) -> Path:
    """A main checkout that uses Lem, with the folder of one task in its state."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem" / "state" / "tasks" / SLUG).mkdir(parents=True)
    (folder / ".lem" / "settings.toml").write_text("")
    (folder / ".lem" / "state" / folders.MARKER).write_bytes(folders.FORM)
    return folder / ".lem" / "state" / "tasks" / SLUG


def started(checkout: Path, source: str = "startup") -> bytes:
    """A SessionStart event of a session in `checkout`."""
    event = {
        "session_id": "c0ffee",
        "transcript_path": "/claude/projects/x/c0ffee.jsonl",
        "source": source,
        "cwd": str(checkout),
        "hook_event_name": "SessionStart",
    }
    return json.dumps(event).encode()


def hooked(
    selector: str, stdin: bytes, **environ: str
) -> subprocess.CompletedProcess[bytes]:
    """Run the manifest's line of `selector` as Claude Code runs it."""
    env = {
        **os.environ,
        "PATH": GUI_PATH,
        "CLAUDE_PLUGIN_ROOT": str(ROOT),
        "LEM_HOOK_BIN": str(HOOK),
        "LEM_TASK": SLUG,
        **environ,
    }
    return subprocess.run(
        ["/bin/sh", "-c", LINES[selector]],
        input=stdin,
        env=env,
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_the_manifest_registers_each_selector_on_its_event_matcher_and_flags() -> None:
    manifest = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    registered = sorted(
        (
            event,
            group.get("matcher"),
            hook["command"],
            hook.get("timeout"),
            hook.get("async", False),
        )
        for event, groups in manifest["hooks"].items()
        for group in groups
        for hook in group["hooks"]
    )
    line = '/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run" {} 2>/dev/null || :'
    assert registered == sorted(
        [
            ("PreCompact", "auto|manual", line.format("precompact"), 5, False),
            ("SessionStart", "startup|resume", line.format("serve"), 5, False),
            (
                "SessionStart",
                "startup|resume|clear|compact|fork",
                line.format("session-start"),
                5,
                False,
            ),
            ("Stop", None, line.format("stop"), None, True),
            ("UserPromptSubmit", None, line.format("corrections"), 10, False),
        ]
    )


def test_with_no_app_every_selector_says_nothing_and_exits_0(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    for selector in SELECTORS:
        ran = hooked(
            selector,
            started(tmp_path / "repo"),
            LEM_HOOK_BIN=str(tmp_path / "missing" / "lem-hook"),
            CLAUDE_ENV_FILE=str(tmp_path / "env"),
        )
        assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), selector
    assert not (folder / sessions.SESSIONS).exists()
    assert not (tmp_path / "env").exists()


def test_with_bad_stdin_every_selector_says_nothing_and_exits_0(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    for selector in SELECTORS:
        for stdin in BAD_INPUTS:
            ran = hooked(selector, stdin, CLAUDE_PROJECT_DIR=str(tmp_path / "repo"))
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), (
                selector,
                stdin,
            )
    assert sessions.read(folder) == ()


def test_session_start_appends_one_framed_line_the_store_reads(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    env_file = tmp_path / "env"
    for source in ("startup", "resume"):
        ran = hooked(
            "session-start",
            started(tmp_path / "repo", source),
            CLAUDE_ENV_FILE=str(env_file),
            AGTERM_SESSION_ID="S-7",
        )
        assert (ran.returncode, ran.stdout) == (0, b"")
    read = sessions.read(folder)
    assert [(line.source, line.claude, line.pane, line.task) for line in read] == [
        ("startup", "c0ffee", "S-7", SLUG),
        ("resume", "c0ffee", "S-7", SLUG),
    ]
    assert read[0].transcript == "/claude/projects/x/c0ffee.jsonl"
    body = (folder / sessions.SESSIONS).read_bytes()
    assert body.startswith(b"\n") and body.endswith(b"}\n")
    assert env_file.read_text() == f"export LEM_PLUGIN_ROOT='{ROOT}'\n" * 2


def test_a_session_that_is_no_tasks_is_put_on_no_record(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    for slug in ("", "Fix_The_Login", "other-task", "-x", "a--b"):
        ran = hooked("session-start", started(tmp_path / "repo"), LEM_TASK=slug)
        assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_an_unwritable_state_folder_is_silent_and_the_plugin_still_kept(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    folder.chmod(0o555)
    try:
        ran = hooked(
            "session-start",
            started(tmp_path / "repo"),
            CLAUDE_ENV_FILE=str(tmp_path / "env"),
        )
    finally:
        folder.chmod(0o755)
    assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b"")
    assert not (folder / sessions.SESSIONS).exists()
    assert (tmp_path / "env").read_text() == f"export LEM_PLUGIN_ROOT='{ROOT}'\n"


def test_on_two_versions_only_session_start_says_the_line(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"version": "0.0.1"}')
    # the plugin's own launcher: the manifest's line runs the one of the plugin it names
    (plugin / "hooks").mkdir()
    shutil.copy2(ROOT / "hooks" / "run", plugin / "hooks" / "run")
    for selector in SELECTORS:
        ran = hooked(
            selector, started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(plugin)
        )
        if selector != "session-start":
            assert (ran.returncode, ran.stdout) == (0, b""), selector
            continue
        said = json.loads(ran.stdout)
        assert said["systemMessage"].startswith(
            f"lem: Lem's plugin 0.0.1 ({plugin}) is behind Lem's app"
        )
    assert not (folder / sessions.SESSIONS).exists()


def test_after_a_compaction_the_task_and_its_handoff_come_back(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "handoff.md").write_text(
        "task: fix-the-login · from build\n\n## Settled\n"
    )
    record = {
        "task": {"status": "building", "hold": None},
        "journal": [
            {"kind": "state", "line": "the plan has 3 tasks"},
            {"kind": "span", "name": "lead"},
            {"kind": "state", "line": "task 2 of 3"},
        ],
    }
    (folder / "task.json").write_text(json.dumps(record))
    ran = hooked("session-start", started(tmp_path / "repo", "compact"))
    said = ran.stdout.decode()
    assert "Lem's task fix-the-login, after the compaction." in said
    assert "status: building; hold: none; newest state line: task 2 of 3" in said
    assert "## Settled" in said
    assert len(sessions.read(folder)) == 1


def test_precompact_gives_the_handoffs_headings_with_the_phase(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "session.md").write_text(
        "Read it.\n\ntask: fix-the-login\nphase: build\n"
    )
    event = json.dumps(
        {
            "cwd": str(tmp_path / "repo"),
            "trigger": "auto",
            "hook_event_name": "PreCompact",
        }
    ).encode()
    said = hooked("precompact", event).stdout.decode()
    assert said.startswith(
        "This summary is the handoff of task fix-the-login, phase build, under five "
        "headings: Settled; Open; Next step; Failed; Changed files"
    )
    assert hooked("precompact", event, LEM_TASK="").stdout == b""


def test_another_lem_first_on_the_path_is_named_and_never_run(tmp_path: Path) -> None:
    workspace(tmp_path / "repo")
    other = tmp_path / "old" / "lem"
    other.parent.mkdir()
    ran_mark = tmp_path / "ran"
    other.write_text(f"#!/bin/sh\ntouch {ran_mark}\n")
    other.chmod(0o755)
    ran = hooked(
        "session-start",
        started(tmp_path / "repo"),
        PATH=f"{other.parent}:{HOOK.parent}:{GUI_PATH}",
    )
    said = json.loads(ran.stdout)
    assert said["systemMessage"] == (
        f"lem: {other} comes first on PATH, and it is not Lem's command "
        f"{HOOK.parent / 'lem'}; the owner puts {HOOK.parent} before {other.parent} in "
        "his PATH"
    )
    assert not ran_mark.exists()


def imported(code: str, stdin: bytes, **environ: str) -> set[str]:
    """The modules that `python -c CODE` imports, from `-X importtime`. The hook is called
    through `main.run`, not its entry, whose `os._exit` would cut off the last lines."""
    ran = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", code],
        input=stdin,
        env={**os.environ, "PATH": GUI_PATH, **environ},
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )
    lines = ran.stderr.decode().splitlines()
    rows = (
        line.rsplit("|", 1)[-1] for line in lines if line.startswith("import time:")
    )
    return {row.strip() for row in rows} - {"package"}


# What `json` brings with it on Python 3.14, which every hook that reads an event pays.
JSON = frozenset(
    (
        "json",
        "_json",
        "re",
        "_sre",
        "enum",
        "functools",
        "_functools",
        "collections",
        "_collections",
        "operator",
        "_operator",
        "keyword",
        "reprlib",
        "types",
        "_types",
        "copyreg",
        "itertools",
    )
)
# What each selector may import beyond Python's own start, by its top-level name: an import a
# later change adds (`pathlib`, `subprocess` on the common path, a library) fails here, on any
# machine and at any load, before it shows in the time of a hook.
ALLOWED = {
    "stop": frozenset(("importlib", "io", "select")),
    "session-start": frozenset(("importlib", "io", "select")) | JSON,
    "precompact": frozenset(("importlib", "io", "select")) | JSON,
    "serve": frozenset(("importlib", "io", "select")) | JSON,
    "corrections": frozenset(
        ("importlib", "io", "select", "tomllib", "datetime", "_datetime", "__future__")
    )
    | JSON,
}


@pytest.mark.parametrize("selector", SELECTORS)
def test_a_selector_imports_only_its_allowed_list(
    selector: str, tmp_path: Path
) -> None:
    workspace(tmp_path / "repo")
    event = json.loads(started(tmp_path / "repo"))
    stdin = json.dumps({**event, "prompt": "fix the login"}).encode()
    start = imported("pass", b"")
    call = f"import os; from lem.hooks import main; main.run({selector!r}, os.environ)"
    hook = imported(call, stdin, LEM_TASK=SLUG, CLAUDE_PLUGIN_ROOT=str(ROOT))
    added = hook - start
    outside = {name.split(".")[0] for name in added} - ALLOWED[selector] - {"lem"}
    lem = {name for name in added if name.split(".")[0] == "lem"}
    assert outside == set()
    assert lem <= {"lem", "lem.hooks"} | {
        name for name in lem if name.startswith("lem.hooks.")
    }
    assert "lem.hooks.main" in lem


def p95(selector: str, stdin: bytes) -> float:
    """The 95th percentile, in milliseconds, of `RUNS` runs of the manifest's line."""
    taken = []
    for _ in range(RUNS):
        began = time.perf_counter()
        hooked(selector, stdin)
        taken.append((time.perf_counter() - began) * 1000)
    taken.sort()
    return taken[math.ceil(0.95 * RUNS) - 1]


# The one-minute load average above which a time is no measure of the hook (the orchestrator's
# decision of 2026-11-25: several builders ran on this Mac, and the same code gave 44 ms at a
# load of 8 and 57 ms at a load of 10). The packaging trial's check P4 measures every selector
# on a quiet machine before the cutover, and is the binding number.
QUIET = 4.0


@pytest.mark.parametrize("selector", SELECTORS)
def test_a_selector_takes_at_most_55_ms_at_p95(selector: str, tmp_path: Path) -> None:
    load = os.getloadavg()[0]
    if load > QUIET:
        pytest.skip(f"load average {load:.1f} over {QUIET}: not measured")
    workspace(tmp_path / "repo")
    took = p95(selector, started(tmp_path / "repo"))
    assert took <= BUDGET, f"{selector}: p95 {took:.1f} ms over {RUNS} runs"


def entry(selector: str, stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    """Run `lem-hook SELECTOR` itself, with no wrapper to mask what it says."""
    env = {**os.environ, "PATH": GUI_PATH, "LEM_TASK": SLUG}
    return subprocess.run(
        [str(HOOK), selector],
        input=stdin,
        env=env,
        cwd=tempfile.gettempdir(),
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_the_entry_itself_says_nothing_and_exits_0_on_any_input(tmp_path: Path) -> None:
    workspace(tmp_path / "repo")
    nul = json.dumps({"cwd": "/tmp/a\u0000b", "hook_event_name": "PreCompact"})
    inputs = (*BAD_INPUTS, nul.encode(), started(tmp_path / "repo\u0000x"))
    for selector in (*SELECTORS, "no-such-selector", ""):
        for stdin in inputs:
            ran = entry(selector, stdin)
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), (
                selector,
                stdin,
            )


def test_a_folder_that_is_gone_puts_nothing_on_record(tmp_path: Path) -> None:
    folder = workspace(tmp_path / "repo")
    gone = tmp_path / "repo" / ".lem" / "worktrees" / SLUG
    ran = hooked("session-start", started(gone))
    assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_a_state_folder_linked_into_another_checkout_is_not_touched(
    tmp_path: Path,
) -> None:
    other = workspace(tmp_path / "other")
    (other / "handoff.md").write_text("task: gift-note · from build\n")
    mine = tmp_path / "mine"
    (mine / ".git").mkdir(parents=True)
    (mine / ".lem").mkdir()
    (mine / ".lem" / "state").symlink_to(tmp_path / "other" / ".lem" / "state")
    for source in ("startup", "compact"):
        ran = hooked("session-start", started(mine, source))
        assert (ran.returncode, ran.stdout) == (0, b"")
    assert not (other / sessions.SESSIONS).exists()


def test_a_link_at_the_environment_file_or_the_sessions_file_is_never_followed(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    target = tmp_path / "target"
    target.write_text("kept\n")
    (tmp_path / "env").symlink_to(target)
    (folder / sessions.SESSIONS).symlink_to(target)
    ran = hooked(
        "session-start",
        started(tmp_path / "repo", "compact"),
        CLAUDE_ENV_FILE=str(tmp_path / "env"),
    )
    assert (ran.returncode, ran.stdout) == (0, b"")
    assert target.read_text() == "kept\n"


def test_a_compaction_whose_line_was_not_kept_or_no_session_start_gives_nothing(
    tmp_path: Path,
) -> None:
    folder = workspace(tmp_path / "repo")
    (folder / "handoff.md").write_text("task: gift-note · from build\n")
    folder.chmod(0o555)
    try:
        failed = hooked("session-start", started(tmp_path / "repo", "compact"))
    finally:
        folder.chmod(0o755)
    other_event = json.loads(started(tmp_path / "repo", "compact"))
    other_event["hook_event_name"] = "PreCompact"
    wrong = hooked("session-start", json.dumps(other_event).encode())
    assert (failed.returncode, failed.stdout) == (0, b"")
    assert (wrong.returncode, wrong.stdout) == (0, b"")
    assert not (folder / sessions.SESSIONS).exists()


def test_a_plugin_whose_manifest_does_not_read_is_named_with_its_fix(
    tmp_path: Path,
) -> None:
    workspace(tmp_path / "repo")
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    shutil.copy2(ROOT / "hooks" / "run", plugin / "hooks" / "run")
    ran = hooked(
        "session-start", started(tmp_path / "repo"), CLAUDE_PLUGIN_ROOT=str(plugin)
    )
    said = json.loads(ran.stdout)["systemMessage"]
    assert said.startswith(
        "lem: Lem cannot tell whether Lem's plugin and Lem's app are two versions: the "
        f"plugin's manifest is unreadable ({plugin}/.claude-plugin/plugin.json"
    )
    assert said.endswith(
        "the owner installs Lem's plugin again and starts the session again"
    )


def files_of(folder: Path) -> dict[str, bytes]:
    """Each file under `folder`, by its path, with its bytes."""
    return {
        str(path): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def test_a_state_folder_of_lem_0_3_is_neither_written_nor_read(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".lem" / "state" / "tasks" / SLUG).mkdir(parents=True)
    (repo / ".lem" / "settings.toml").write_text("")
    (repo / ".lem" / "state" / "events.jsonl").write_text('{"event": "task.state"}\n')
    (repo / ".lem" / "state" / "tasks" / SLUG / "state.md").write_text("building\n")
    (repo / ".lem" / "state" / "tasks" / SLUG / "handoff.md").write_text("task: x\n")
    before = files_of(repo)
    compact = json.loads(started(repo, "compact"))
    inputs = (
        started(repo),
        json.dumps(compact).encode(),
        json.dumps({**compact, "hook_event_name": "PreCompact"}).encode(),
        json.dumps({"prompt": "fix the login", "cwd": str(repo)}).encode(),
    )
    for selector in SELECTORS:
        for stdin in inputs:
            ran = hooked(selector, stdin)
            assert (ran.returncode, ran.stdout, ran.stderr) == (0, b"", b""), selector
    assert files_of(repo) == before

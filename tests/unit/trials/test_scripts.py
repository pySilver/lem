"""The trial scripts' input, evidence and count rules, without any trial command."""

import hashlib
import importlib.util
import json
import shlex
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

BIN = (
    Path(__file__).resolve().parents[3]
    / "docs/plans/2026-11-25-lem-built-again/trials/bin"
)


def script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"trial_{name}", BIN / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_entry_clears_the_environment_and_quotes_its_trial_paths(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "a 'trial'"
    make = script("make")
    for gui in (False, True):
        entry = make.entry(folder, "trial", gui_path=gui)
        words = shlex.split(entry.splitlines()[-1])
        assert words[:3] == ["exec", "/usr/bin/env", "-i"]
        environ = dict(word.split("=", 1) for word in words[3:-1])
        assert environ["HOME"] == str(folder / "home")
        assert environ["XDG_CONFIG_HOME"] == str(folder / "config")
        assert environ["GH_CONFIG_DIR"] == str(folder / "config/gh")
        assert environ["PATH"] == (
            "/usr/bin:/bin" if gui else f"{folder / 'bin'}:/usr/bin:/bin"
        )
        assert environ["LEM_SERVE"] == "off"
        assert "GH_TOKEN" not in environ
        assert len(environ) == len(words[3:-1])


def test_step_paths_cannot_escape_the_trial(tmp_path: Path) -> None:
    step = script("step")
    assert step.inside(tmp_path, Path("repo")) == tmp_path / "repo"
    (tmp_path / "other").symlink_to(tmp_path.parent, target_is_directory=True)
    for path in ("../elsewhere", "other/repo"):
        with pytest.raises(ValueError, match="must be in"):
            step.inside(tmp_path, Path(path))


def test_p95_uses_the_nearest_rank_of_the_sorted_samples() -> None:
    p95 = script("p95")
    assert p95.percentile(list(range(30, 0, -1))) == 29
    assert p95.percentile([16.0]) == 16


def test_timing_reads_every_installed_manifest_line_once(tmp_path: Path) -> None:
    p95 = script("p95")
    manifest = BIN.parents[4] / "hooks/hooks.json"
    assert tuple(p95.lines(manifest)) == (
        "corrections",
        "serve",
        "session-start",
        "precompact",
        "stop",
    )
    bad = tmp_path / "bad.json"
    table = json.loads(manifest.read_bytes())
    table["hooks"]["Stop"] *= 2
    bad.write_text(json.dumps(table))
    with pytest.raises(ValueError, match="unexpected hook under Stop"):
        p95.lines(bad)
    del table["hooks"]["Stop"]
    bad.write_text(json.dumps(table))
    with pytest.raises(ValueError, match="expected every selector"):
        p95.lines(bad)


def test_merge_count_counts_only_calls_forwarded_to_real_gh(tmp_path: Path) -> None:
    merge = script("merge_calls")
    assert merge.count(tmp_path)["sent"] == 0
    merge.note(tmp_path, "before-send")
    assert merge.count(tmp_path)["sent"] == 0
    merge.note(tmp_path, "sending", pr="21")
    merge.note(tmp_path, "reply", exit=0)
    merge.note(tmp_path, "read-reply-lost")
    row = merge.count(tmp_path)
    assert row["sent"] == 1
    assert [event["event"] for event in row["events"]] == [
        "before-send",
        "sending",
        "reply",
        "read-reply-lost",
    ]


def test_merge_refuses_a_different_repository_head_and_branch() -> None:
    merge = script("merge_calls")
    tip = "a" * 40
    words = ["pr", "merge", "21", "--match-head-commit", tip, "--repo", merge.REPO]
    assert merge.merge_target(words, "21") == tip
    with pytest.raises(ValueError, match="only the named PR"):
        merge.merge_target(words, "22")
    with pytest.raises(ValueError, match="only the named PR"):
        merge.merge_target([*words[:-1], "someone/else"], "21")
    request = {
        "headRefName": "trial-21-head",
        "baseRefName": "trial-21-base",
        "state": "OPEN",
        "headRefOid": tip,
    }
    assert merge.checked(request, tip) is None
    with pytest.raises(ValueError, match="pinned head"):
        merge.checked(request, "b" * 40)
    with pytest.raises(ValueError, match=r"trial-\*"):
        merge.checked({**request, "baseRefName": "main"}, tip)


def test_index_includes_a_cut_step_and_hashes_raw_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    row = {"name": "r5", "state": "started"}
    (evidence / "r5.meta.json").write_text(json.dumps(row))
    (evidence / "r5.err").write_bytes(b"partial\n")
    (evidence / "manual").mkdir()
    (evidence / "manual/capture").touch()
    found = script("index").index(tmp_path)
    assert found["steps"] == {"r5": row}
    assert found["files"]["r5.err"] == {
        "bytes": 8,
        "sha256": hashlib.sha256(b"partial\n").hexdigest(),
    }
    assert "manual/capture" in found["files"]
    (evidence / "link").symlink_to(evidence / "r5.err")
    with pytest.raises(ValueError, match="keep a copy"):
        script("index").index(tmp_path)

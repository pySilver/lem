"""`lem doctor` as the owner runs it: its words, its envelope on a machine that has what Lem
requires and on one that lacks git, and the tier of each tool as the install guide says it."""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from lem.cli.doctor.rows import gathered
from unit.settings.doctor.stage import Stage

if TYPE_CHECKING:
    from collections.abc import Mapping

ROOT = Path(__file__).resolve().parents[4]
# What no leaf may load when it is imported (tests/unit/cli/test_tree.py).
HEAVY = ("starlette", "uvicorn", "jinja2", "httpx", "tomlkit", "psutil", "pywebpush")
TOOLS = (
    "git",
    "revmux",
    "agtermctl",
    "gh",
    "plannotator-tui",
    "plannotator",
    "codex",
    "claude",
    "mailbox-chat.py",
    "cronn",
)
SKILLS = ("revmux", "agterm", "webrev", "agdoc", "backlog", "mailbox-chat")
# What a call must not take from the environment of the test's own shell.
OWN = ("CRONN_", "JEV_", "AGTERM_", "CLAUDE_", "LEM_PLUGIN_ROOT", "LEM_HOOK_BIN")
# Each row of the check that the table of docs/install.md lists, with the words of the one
# table row that names it.
IN_TABLE = (
    ("agterm", "[agterm]"),
    ("agterm skill", "[agterm]"),
    ("claude", "[Claude Code]"),
    ("git", "git, and Python"),
    ("python3", "git, and Python"),
    ("revmux", "[revmux]"),
    ("revmux skill", "[revmux]"),
    ("cronn", "[cronn]"),
    ("mailbox-chat", "the mailbox chat"),
    ("mailbox-chat skill", "the mailbox chat"),
    ("webrev skill", "webrev"),
    ("backlog skill", "the backlog recipe"),
    ("agdoc skill", "agdoc"),
    ("codex", "[Codex]"),
    ("plannotator", "[Plannotator]"),
    ("Jev key", "JEV_API_KEY"),
)
# A table row whose word and the check's tier do not agree, and why it is not settled here: gh
# is optional (a machine may hold repositories that do not land on GitHub), and the table lists
# it with no word, as needed (the maintaining session, 2026-11-21).
UNSETTLED = ("the [GitHub CLI]",)
TABLE = re.compile(
    r"^\| Tool \| Lem uses it for \|\n\| --- \| --- \|\n((?:\|.*\n)+)", re.MULTILINE
)
TIER = re.compile(r":\s*(optional|highly recommended|recommended)$")


def furnished(stage: Stage) -> Stage:
    """Every tool, every skill in the home, and Lem's builder from a plugin for the user."""
    for name in TOOLS:
        stage.tool(name)
    for name in SKILLS:
        stage.write(f"home/.claude/skills/{name}/SKILL.md", "x")
    stage.mailbox_settings()
    stage.plugins(
        {
            "plugins": {
                "lem@lem": [{"scope": "user", "installPath": str(stage.root / "x")}]
            }
        }
    )
    return stage


def environment(stage: Stage, **given: str) -> Mapping[str, str]:
    """The environment of a call: the test's own, with no tool of the shell that started the
    test, the stand-ins and this checkout's .venv on the PATH, and its lem-hook for hooks/run."""
    kept = {
        name: value for name, value in os.environ.items() if not name.startswith(OWN)
    }
    venv = Path(sys.executable).parent
    return {
        **kept,
        "HOME": str(stage.home),
        "XDG_CONFIG_HOME": str(stage.config),
        "PATH": f"{stage.bin}:{venv}",
        "LEM_HOOK_BIN": str(venv / "lem-hook"),
        **given,
    }


def test_lem_doctor_help_prints_its_usage_and_a_word_more_is_a_wrong_call(
    tmp_path: Path,
) -> None:
    helped = lem("doctor", "--help", cwd=tmp_path)
    assert (helped.code, helped.stdout.startswith("Usage: lem doctor")) == (0, True)
    wrong = lem("doctor", "now", cwd=tmp_path)
    assert (wrong.code, wrong.stdout) == (2, "")
    assert "Usage: lem doctor" in wrong.stderr


def test_a_machine_with_what_lem_requires_passes_with_every_row(tmp_path: Path) -> None:
    stage = furnished(Stage(tmp_path))
    ran = lem("doctor", cwd=stage.work, env=environment(stage))
    assert ran.code == 0, ran
    found = ran.envelope()
    assert found["ok"] is True
    assert "refusal" not in found
    result = ran.result()
    assert isinstance(result, dict)
    assert result["ok"] is True
    rows = {row["name"]: row for row in result["rows"]}
    assert not [
        row for row in rows.values() if row["need"] == "required" and not row["found"]
    ]
    for name in (
        "mailbox-chat",
        "Lem's versions",
        "lem on PATH",
        "hooks/run finds lem-hook",
        "folders of Lem 0.3",
    ):
        assert rows[name]["found"] is True, rows[name]


def test_doctor_refuses_an_installed_mailbox_with_no_waiter(tmp_path: Path) -> None:
    stage = furnished(Stage(tmp_path))
    stage.write("home/.claude/settings.json", "{}")
    ran = lem("doctor", cwd=stage.work, env=environment(stage))
    assert ran.code == 1, ran
    refusal = ran.envelope()["refusal"]
    assert isinstance(refusal, dict)
    assert refusal["why"] == "this machine lacks what Lem requires: mailbox-chat"
    assert "`mailbox-chat.py claude-hook` with `asyncRewake: true`" in ran.stdout


def test_without_git_the_check_exits_1_with_its_rows_and_the_refusal_that_names_git(
    tmp_path: Path,
) -> None:
    stage = furnished(Stage(tmp_path))
    (stage.bin / "git").unlink()
    ran = lem("doctor", cwd=stage.work, env=environment(stage))
    assert ran.code == 1, ran
    found = ran.envelope()
    assert found["ok"] is False
    refusal = found["refusal"]
    assert isinstance(refusal, dict)
    assert (refusal["code"], refusal["why"]) == (
        "doctor",
        "this machine lacks what Lem requires: git",
    )
    result = ran.result()
    assert isinstance(result, dict)
    assert result["ok"] is False
    names = [row["name"] for row in result["rows"]]
    assert {"git", "revmux", "claude", "cronn", "board server"} <= set(names)
    said = ran.stdout.lower()
    assert "question page" not in said
    assert "lem jev" not in said
    assert not [name for name in names if name.startswith(("ask", "lem-ask"))]


def table() -> list[tuple[str, str]]:
    """Each row of the table under "What you need" in docs/install.md: its first cell, and the
    word for its tier, `required` when the cell has none."""
    text = (ROOT / "docs" / "install.md").read_text(encoding="utf-8")
    found = TABLE.search(text)
    if found is None:
        return []
    rows = []
    for line in found[1].splitlines():
        cell = line.split(" | ")[0].lstrip("| ")
        word = TIER.search(cell)
        tier = word[1] if word else "required"
        rows.append((cell, "recommended" if tier == "highly recommended" else tier))
    return rows


def test_the_install_guide_says_each_tools_tier_as_the_machine_check_has_it(
    tmp_path: Path,
) -> None:
    rows = table()
    assert rows, 'docs/install.md has no table under "What you need"'
    needs = {row.name: row.need for row in gathered(furnished(Stage(tmp_path)).look())}
    for name, words in IN_TABLE:
        named = [tier for cell, tier in rows if words in cell]
        assert len(named) == 1, f"one row of the install table names {words!r}"
        assert needs[name] == named[0], (name, needs[name], named[0])
    bound = [words for _, words in IN_TABLE] + list(UNSETTLED)
    for cell, _ in rows:
        assert any(words in cell for words in bound), cell


@pytest.mark.parametrize("word", ["lem settings set load.start", "lem serve ensure"])
def test_the_rows_name_the_commands_of_this_lem(tmp_path: Path, word: str) -> None:
    stage = furnished(Stage(tmp_path))
    said = str(gathered(stage.look()))
    assert word in said
    for old in (
        "lem project load",
        "lem project handoff",
        "serve --ensure",
        "--push-test",
    ):
        assert old not in said


def test_the_leaf_loads_no_heavy_library_and_no_other_noun() -> None:
    probe = (
        "import sys; from lem.cli import lazy; lazy.main(['doctor', '--help']); "
        "print(' '.join(sorted(sys.modules)))"
    )
    ran = subprocess.run(
        [sys.executable, "-I", "-B", "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = ran.stdout.splitlines()[-1].split()
    assert [name for name in loaded if name.split(".")[0] in HEAVY] == []
    nouns = {name.split(".")[2] for name in loaded if name.startswith("lem.cli.")}
    assert nouns <= {"doctor", "lazy", "nouns", "output", "place", "group"}, nouns

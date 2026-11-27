"""The rows of the programs on PATH, the agents and the skills: each found or not on a PATH of
stand-ins, with its need, its version, its guide and what happens without it."""

import json
from typing import TYPE_CHECKING

import pytest

from lem.cli.doctor import agents, skill_words, tool_words
from lem.cli.doctor.row import reported
from lem.cli.doctor.rows import gathered
from lem.cli.doctor.skills import skill_row
from lem.cli.doctor.tools import cronn_row, gh_row, python_row, tool_row
from unit.settings.doctor.stage import Stage, named, names

if TYPE_CHECKING:
    from pathlib import Path

# Every program a machine that runs Lem has, but git.
TOOLS = (
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


@pytest.fixture
def stage(tmp_path: Path) -> Stage:
    """A machine of its own for each case."""
    return Stage(tmp_path)


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


def test_a_program_on_path_is_found_with_the_version_it_prints(stage: Stage) -> None:
    stage.tool("revmux", "revmux 0.9.1")
    row = tool_row(stage.look(), tool_words.REVMUX)
    assert (row.name, row.need, row.found, row.detail) == (
        "revmux",
        "required",
        True,
        "revmux 0.9.1",
    )
    absent = tool_row(stage.look(), tool_words.GIT)
    assert (absent.found, absent.detail, absent.without_it) == (
        False,
        None,
        "nothing runs",
    )


def test_without_git_the_check_fails_and_still_gives_every_other_row(
    stage: Stage,
) -> None:
    rows = gathered(furnished(stage).look())
    git = named(rows, "git")
    assert (git.need, git.found) == ("required", False)
    assert not reported(rows).ok
    for name in ("revmux", "agterm", "claude", "cronn", "hook modules", "lem on PATH"):
        assert name in names(rows)


def test_the_review_tool_comes_before_the_pull_request_and_without_it_the_check_fails(
    stage: Stage,
) -> None:
    furnished(stage).tool("git")
    (stage.bin / "revmux").unlink()
    rows = gathered(stage.look())
    revmux = named(rows, "revmux")
    assert (revmux.need, revmux.found) == ("required", False)
    assert "review rounds before the pull request" in revmux.used_for
    assert "it is not proposed" in (revmux.without_it or "")
    assert named(rows, "claude").need == "required"
    assert "revmux" in [
        row.name for row in rows if row.need == "required" and not row.found
    ]


def test_the_review_tool_alone_is_not_enough_and_no_agterm_skill_row_without_agterm(
    stage: Stage,
) -> None:
    stage.tool("revmux")
    rows = gathered(stage.look())
    needed = {row.name: row.need for row in rows}
    for name in ("revmux skill", "agterm", "mailbox-chat", "mailbox-chat skill"):
        assert needed[name] == "required", name
    assert "agterm skill" not in needed
    assert "task picker" not in needed


def test_agterm_without_its_skill_fails_and_says_outside_a_session(
    stage: Stage,
) -> None:
    stage.tool("agtermctl", "agterm 2.4")
    rows = agents.agterm_rows(stage.look())
    assert names(rows) == ["agterm", "agterm skill", "task picker"]
    assert (rows[0].found, rows[0].in_session) == (True, False)
    assert (rows[1].need, rows[1].found) == ("required", False)
    inside = agents.agterm_rows(stage.look(AGTERM_SESSION_ID="s1"))
    assert inside[0].in_session is True
    stage.write("home/.agents/skills/agterm/SKILL.md", "x")
    assert agents.agterm_rows(stage.look())[1].found


def test_gh_is_optional_found_not_signed_in_or_signed_in(stage: Stage) -> None:
    absent = gh_row(stage.look())
    assert (absent.need, absent.found, absent.signed_in) == ("optional", False, False)
    stage.tool("gh", "gh version 2.80", code=1)
    out = gh_row(stage.look())
    assert (out.found, out.signed_in) == (True, False)
    assert out.detail is not None
    assert "`gh auth login` signs it in" in out.detail
    stage.write("bin/gh", "#!/bin/sh\necho 'gh version 2.80'\nexit 0\n")
    signed = gh_row(stage.look())
    assert (signed.found, signed.signed_in, signed.detail) == (
        True,
        True,
        "gh version 2.80",
    )


def test_cronn_is_required_says_where_to_get_it_and_names_no_free_hour(
    stage: Stage,
) -> None:
    absent = cronn_row(stage.look())
    assert (absent.need, absent.found, absent.running) == ("required", False, False)
    assert "https://cronn.umputun.dev" in (absent.without_it or "")
    assert "free hour" not in json.dumps([absent.used_for, absent.without_it])


def test_an_installed_cronn_that_does_not_answer_is_not_running(stage: Stage) -> None:
    stage.tool("cronn")
    assert cronn_row(stage.look()).running is False
    assert stage.asked == []
    stage.write("home/.config/cronn/cronn.env", 'A=1\nCRONN_PORT="8432"\n')
    assert cronn_row(stage.look()).running is False
    stage.answering = True
    assert cronn_row(stage.look()).running is True
    assert stage.asked == [8432, 8432]
    stage.write("elsewhere/cronn.env", "CRONN_PORT=9000\n")
    cronn_row(stage.look(CRONN_CONFIG_DIR=str(stage.root / "elsewhere")))
    assert stage.asked[-1] == 9000


def test_with_no_codex_its_row_is_highly_recommended_and_there_is_no_persona_row(
    stage: Stage,
) -> None:
    rows = agents.codex_rows(stage.look())
    assert names(rows) == ["codex"]
    said = rows[0].without_it or ""
    assert (rows[0].need, rows[0].found) == ("recommended", False)
    assert said.startswith("highly recommended, since without it Claude reviews")
    for words in ("second Claude", "not green", "one model family"):
        assert words in said
    assert rows[0].guide == "https://github.com/openai/codex"


def test_codex_gets_a_row_for_the_persona_agent_whose_absence_fails_nothing(
    stage: Stage,
) -> None:
    stage.tool("codex", "codex-cli 0.80")
    rows = agents.codex_rows(stage.look())
    assert names(rows) == ["codex", "codex persona agent"]
    assert (rows[1].need, rows[1].found) == ("optional", False)
    stage.write("home/.codex/agents/persona.toml", "x")
    assert agents.codex_rows(stage.look())[1].found


def test_plannotator_is_optional_with_its_guide_and_the_version_found(
    stage: Stage,
) -> None:
    stage.tool("plannotator", "plannotator 0.29.0")
    row = tool_row(stage.look(), tool_words.PLANNOTATOR)
    assert (row.name, row.need, row.found, row.detail) == (
        "plannotator",
        "optional",
        True,
        "plannotator 0.29.0",
    )
    assert row.guide == "https://plannotator.ai/inbox/"
    assert "Plannotator Inbox" in row.used_for
    assert "while he is away" in row.used_for


def test_without_plannotator_the_row_says_that_nothing_goes_to_the_inbox(
    stage: Stage,
) -> None:
    row = tool_row(stage.look(), tool_words.PLANNOTATOR)
    assert (row.need, row.found, row.detail) == ("optional", False, None)
    assert (row.without_it or "").startswith("nothing goes to the Plannotator Inbox")


def test_plannotator_tui_is_recommended_with_its_guide(stage: Stage) -> None:
    row = tool_row(stage.look(), tool_words.PLANNOTATOR_TUI)
    assert (row.need, row.found) == ("recommended", False)
    assert row.guide is not None
    assert row.guide.endswith("annotate-in-plannotator-tui")


def test_the_python_row_names_the_apps_own_interpreter(stage: Stage) -> None:
    row = python_row(stage.look())
    assert (row.name, row.need, row.found) == ("python3", "required", True)
    assert row.detail is not None
    assert str(stage.app / "bin" / "python") in row.detail


def test_webrev_and_the_backlog_are_required_and_agdoc_recommended_each_with_a_guide(
    stage: Stage,
) -> None:
    look = stage.look()
    for skill, need in (
        (skill_words.WEBREV, "required"),
        (skill_words.BACKLOG, "required"),
        (skill_words.AGDOC, "recommended"),
    ):
        row = skill_row(look, skill)
        assert (row.need, row.found) == (need, False), skill.name
        assert row.guide is not None
        assert row.guide.startswith(tool_words.COOKBOOK)


def test_a_skill_counts_in_a_skills_folder_of_the_user_or_of_the_repository(
    stage: Stage,
) -> None:
    checkout = stage.repository()
    stage.write("repo/.claude/skills/backlog/SKILL.md", "x")
    row = skill_row(stage.look(checkout), skill_words.BACKLOG)
    assert (row.found, row.detail) == (
        True,
        str(checkout.resolve() / ".claude" / "skills" / "backlog"),
    )
    stage.write("home/.codex/skills/webrev/SKILL.md", "x")
    assert skill_row(stage.look(), skill_words.WEBREV).found


def test_a_skill_counts_in_a_plugin_of_its_name_or_carried_by_a_plugin_of_another(
    stage: Stage,
) -> None:
    carried = stage.write("cache/tracking/skills/backlog/SKILL.md", "x").parents[2]
    stage.plugins(
        {
            "version": 2,
            "plugins": {
                "webrev@cookbook": [
                    {"scope": "user", "installPath": str(stage.root / "x")}
                ],
                "tracking@cookbook": [{"scope": "user", "installPath": str(carried)}],
            },
        }
    )
    look = stage.look()
    assert skill_row(look, skill_words.WEBREV).detail == "the plugin webrev@cookbook"
    assert skill_row(look, skill_words.BACKLOG).detail == "the skill tracking:backlog"


def test_a_plugin_list_of_another_shape_is_no_answer_and_the_cache_counts(
    stage: Stage,
) -> None:
    stage.write(
        "home/.claude/plugins/installed_plugins.json", '{"plugins": ["webrev"]}'
    )
    look = stage.look()
    assert not skill_row(look, skill_words.WEBREV).found
    stage.write(
        "home/.claude/plugins/cache/cookbook/webrev/1.0/skills/webrev/SKILL.md", "x"
    )
    assert skill_row(look, skill_words.WEBREV).found
    stage.plugins({"plugins": {"agdoc@x": [{"installPath": str(stage.root / "x")}]}})
    assert not skill_row(look, skill_words.AGDOC).found


def test_without_claude_code_the_check_fails_and_there_is_no_builder_row(
    stage: Stage,
) -> None:
    rows = agents.claude_rows(stage.look())
    assert names(rows) == ["claude"]
    assert (rows[0].need, rows[0].found) == ("required", False)


def test_claude_code_without_the_builder_fails_and_a_builder_file_in_the_home_is_not_lems(
    stage: Stage,
) -> None:
    stage.tool("claude", "2.1.330 (Claude Code)")
    stage.write("home/.claude/agents/lem-builder.md", "x")
    rows = agents.claude_rows(stage.look())
    builder = rows[1]
    assert (builder.name, builder.need, builder.found) == (
        "lem-builder agent",
        "required",
        False,
    )
    assert "claude plugin install lem@lem --scope project" in (builder.without_it or "")


def test_the_builder_comes_from_lems_plugin_for_the_user_or_this_repository(
    stage: Stage,
) -> None:
    stage.tool("claude")
    checkout = stage.repository()
    other = stage.repository("other")
    stage.plugins(
        {"plugins": {"lem@lem": [{"scope": "project", "projectPath": str(other)}]}}
    )
    assert not agents.claude_rows(stage.look(checkout))[1].found
    stage.plugins({"plugins": {"lem@lem": [{"scope": "local"}]}})
    assert not agents.claude_rows(stage.look(checkout))[1].found
    stage.plugins(
        {"plugins": {"lem@lem": [{"scope": "project", "projectPath": str(checkout)}]}}
    )
    row = agents.claude_rows(stage.look(checkout))[1]
    assert (row.found, row.detail) == (True, "lem:lem-builder, from the plugin lem@lem")
    stage.plugins({"plugins": {"lem@lem": [{"scope": "user"}]}})
    assert agents.claude_rows(stage.look())[1].found


def test_a_plugin_loaded_by_a_flag_counts_through_claude_plugin_root(
    stage: Stage,
) -> None:
    stage.tool("claude")
    loaded = stage.root / "plugin"
    stage.write("plugin/agents/lem-builder.md", "x")
    row = agents.claude_rows(stage.look(CLAUDE_PLUGIN_ROOT=str(loaded)))[1]
    assert row.found
    assert row.detail == (
        f"lem:lem-builder, from the plugin loaded for this session ({loaded})"
    )
    another = stage.root / "another"
    another.mkdir()
    row = agents.claude_rows(stage.look(CLAUDE_PLUGIN_ROOT=str(another)))[1]
    assert not row.found
    assert "CLAUDE_PLUGIN_ROOT" in (row.without_it or "")


def test_a_tasks_worktree_finds_the_projects_own_builder_in_the_main_checkout(
    stage: Stage,
) -> None:
    stage.tool("claude")
    checkout = stage.repository()
    stage.write("repo/.claude/agents/lem-builder.md", "x")
    tree = stage.worktree(checkout, "gift-note")
    row = agents.claude_rows(stage.look(tree))[1]
    assert row.found
    assert row.detail == str(
        checkout.resolve() / ".claude" / "agents" / "lem-builder.md"
    )
    assert "claude plugin install lem@lem" in (row.without_it or "")
    assert "setup" not in (row.without_it or "")

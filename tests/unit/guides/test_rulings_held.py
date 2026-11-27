"""The owner's rulings on what Lem is and on its README, guides and logo, each held by the place
that says it: the guides, the README, AGENTS.md, the skills and the package."""

import re
import tomllib
from pathlib import Path

from unit.guides.test_install import tool_groups

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
SKILLS = ROOT / "skills"
# The skills Lem ships, each named lem-NAME and called as /lem NAME.
SHIPPED = {
    "lem",
    "lem-ask",
    "lem-ask-expert",
    "lem-dialectic",
    "lem-gate",
    "lem-github",
    "lem-interview-me",
    "lem-linear",
    "lem-panel",
    "lem-root-cause",
}
# "Opinionated": what the owner put out of scope, and the core's leavers, as a skill's name.
OUT_OF_SCOPE = re.compile(
    r"peer-planning|activation|language-server|output-style|brainstorm|clipboard|writing-style"
    r"|release|last-tag|annotate|backlog"
)
# Words of a text that tells history or a reason for a change, which a text for a reader leaves out.
HISTORY = re.compile(
    r"\b(previously|used to|no longer|was renamed|is now|formerly|changelog)\b",
    re.IGNORECASE,
)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def flat(path: str) -> str:
    return " ".join(text(path).split())


def guides() -> list[Path]:
    config = tomllib.loads(text("zensical.toml"))
    return [DOCS / next(iter(entry.values())) for entry in config["project"]["nav"]]


def test_lem_is_an_app_and_its_plugin_installed_in_two_steps() -> None:
    install = flat("docs/install.md")
    assert (
        "Lem has two parts: the app, with the command `lem`, and the plugin" in install
    )
    assert "brew install pySilver/tap/lem" in install
    assert "claude plugin install lem@lem --scope project" in install


def test_the_app_ships_from_the_owners_tap_and_a_mismatch_names_the_part_behind() -> (
    None
):
    assert "brew install pySilver/tap/lem" in text("README.md")
    update = flat("docs/update.md")
    assert "brew upgrade pySilver/tap/lem" in update
    assert "one line that names the part that is behind" in update


def test_the_command_keeps_the_name_lem() -> None:
    project = tomllib.loads(text("pyproject.toml"))
    assert project["project"]["scripts"]["lem"] == "lem.__main__:main"


def test_one_lem_for_one_repository_the_plugin_installs_for_the_project() -> None:
    for path in ("README.md", "docs/index.md", "docs/install.md"):
        lines = re.findall(r"^claude plugin \S+ .*$", text(path), flags=re.MULTILINE)
        assert lines, path
        assert all(line.endswith("--scope project") for line in lines), path


def test_claude_code_and_agterm_first_and_codex_for_reviews() -> None:
    harness = {path.name for path in (SKILLS / "lem/harness").iterdir()}
    assert harness == {"README.md", "claude-code.md", "claude-code"}
    groups = tool_groups(text("docs/install.md"))
    assert "[Codex](https://github.com/openai/codex)" in groups["Recommended"]
    assert "Lem needs [agterm](https://agterm.com)" in text("docs/index.md")


def test_opinionated_no_shipped_skill_is_out_of_scope_and_the_set_is_the_ten() -> None:
    names = {path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()}
    assert names == SHIPPED
    assert [name for name in names if OUT_OF_SCOPE.search(name)] == []


def test_release_last_tag_and_another_persons_review_left_the_core_for_the_add_on_list() -> (
    None
):
    assert (DOCS / "backlog/add-ons-after-the-core.md").is_file()
    stages = {path.stem for path in (SKILLS / "lem/stages").glob("*.md")}
    assert not stages & {"release", "last-tag", "review-pr"}


def test_three_commands_are_no_commands_of_his_and_two_recipes_are_required() -> None:
    required = tool_groups(text("docs/install.md"))["Required"]
    for recipe in ("mailbox-chat", "webrev skill", "backlog skill"):
        assert f"- [{recipe}](" in required
    for path in guides():
        assert "/lem annotate" not in path.read_text(encoding="utf-8"), path
        assert "lem-backlog" not in path.read_text(encoding="utf-8"), path


def test_the_shipped_skills_start_only_for_lem() -> None:
    for name in SHIPPED - {"lem"}:
        head = (
            (SKILLS / name / "SKILL.md")
            .read_text(encoding="utf-8")
            .split("\n---", 1)[0]
        )
        assert "disable-model-invocation: true" in head, name
    assert "plain words also start a\nskill" in text("docs/index.md")


def test_a_shipped_skills_name_follows_lem_as_agents_md_says() -> None:
    agents = flat("AGENTS.md")
    assert "`lem-NAME`, which the owner calls as `/lem NAME`" in agents
    assert all(name == "lem" or name.startswith("lem-") for name in SHIPPED)


def test_what_he_names_in_the_interview_is_a_direction_the_plan_follows() -> None:
    assert "The plan uses a library or an approach that you name." in flat(
        "docs/flow.md"
    )


def test_lem_is_his_one_desk_from_a_request_to_a_merged_pull_request() -> None:
    home = text("docs/index.md")
    chart = home.split("```mermaid\n", 1)[1].split("```", 1)[0]
    assert 'request["Your request"]' in chart
    assert 'merged["Merged"]' in chart


def test_lem_is_for_experienced_developers_and_a_change_is_measured_on_a_small_task() -> (
    None
):
    agents = flat("AGENTS.md")
    assert "A change is measured by what it costs a developer on a small task" in agents
    required = tool_groups(text("docs/install.md"))["Required"]
    assert "[Claude Code](https://code.claude.com/docs) for the agents." in required


def test_the_rules_of_a_project_and_another_programs_settings_stay_where_they_are() -> (
    None
):
    harness = flat("skills/lem/harness/claude-code.md")
    assert "Claude Code loads `.claude/rules/` by itself" in harness
    assert "`.revmux`, that tool's own" in flat("skills/lem/stages/init.md")
    for path in (*SKILLS.rglob("*.md"), *guides()):
        words = path.read_text(encoding="utf-8")
        assert not re.search(r"(mv|ln -s|git mv)\s+\.(claude/rules|revmux)", words), (
            path
        )


def test_lems_docs_do_not_speak_for_another_tool() -> None:
    remove = text("docs/update.md").split("## Remove", 1)[1]
    assert ".revmux" not in remove
    assert "cronn jobs of this repository" in remove


def test_no_history_and_no_reasons_in_a_text_for_a_reader() -> None:
    for path in [*guides(), ROOT / "README.md"]:
        found = HISTORY.findall(path.read_text(encoding="utf-8"))
        assert found == [], (path.name, found)


def test_the_logo_is_the_scene_with_its_night_file_in_the_readme_and_the_home_page() -> (
    None
):
    readme = text("README.md")
    assert (
        '<source media="(prefers-color-scheme: dark)" srcset="assets/lem-night.svg">'
        in readme
    )
    assert '<img src="assets/lem.svg"' in readme
    home = text("landing/index.html")
    assert 'srcset="docs/assets/lem-night.svg"' in home
    assert '<img src="docs/assets/lem.svg"' in home
    assert (ROOT / "docs/assets/lem.svg").resolve() == (
        ROOT / "assets/lem.svg"
    ).resolve()


def test_the_readme_tells_the_commands_he_types_and_no_job_that_runs_by_itself() -> (
    None
):
    home = text("docs/index.md")
    table = home.split("## What you type", 1)[1].split("\n\n", 2)[1]
    commands = [row.split(" | ")[0].lstrip("| ") for row in table.splitlines()[2:]]
    assert commands
    assert all(command.startswith(("`/lem", "a chord")) for command in commands), (
        commands
    )
    assert "/lem retro" not in table
    assert "/lem night" not in table


def test_the_texts_assume_a_public_repository() -> None:
    for path in ("README.md", "docs/install.md"):
        words = text(path).lower()
        assert "access token" not in words, path
        assert "private repository" not in words, path


def test_the_skill_files_keep_their_own_voice_and_the_texts_people_read_say_the_owner() -> (
    None
):
    agents = flat("AGENTS.md")
    assert "comments, docstrings and the stage files keep their voice" in agents
    assert 'its texts say "the owner".' in agents


def test_the_tests_are_chosen_by_what_can_fail_in_the_loop_of_checks() -> None:
    checks = text("AGENTS.md").split("## Checks", 1)[1].split("\n## ", 1)[0]
    assert "The loop:" in checks
    assert "A rule that takes facts and returns a result is a unit\ncase" in checks

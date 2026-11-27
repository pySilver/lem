"""The install guide has the same groups and recipe links as the doctor, and the Homebrew lines
the doctor gives on a machine with none of the programs."""

import re
from typing import TYPE_CHECKING

from lem.cli.doctor.row import reported
from lem.cli.doctor.rows import gathered, guarded
from lem.cli.doctor.tool_parts import TOOL_PARTS
from unit.guides.test_guides import text_of
from unit.settings.doctor.stage import Stage

if TYPE_CHECKING:
    from pathlib import Path

# The rows that come with Lem itself: the app's own Python and the plugin's builder. The guide
# lists only what a developer installs.
WITH_LEM = {"python3", "lem-builder agent"}
ROW_NAMES = {
    "Claude Code": "claude",
    "Codex": "codex",
    "GitHub CLI": "gh",
    "Plannotator Inbox": "plannotator",
    "JEV_API_KEY": "Jev key",
}


def tool_groups(guide: str) -> dict[str, str]:
    """The tool lists under What you need, by heading."""
    needs = guide.split("## What you need\n", 1)[1]
    tools = needs.split("\n## ", 1)[0]
    groups = re.split(r"^### (.+)\n", tools, flags=re.MULTILINE)
    assert groups[1::2] == ["Required", "Recommended", "Optional"]
    return dict(zip(groups[1::2], groups[2::2], strict=True))


def test_the_install_guide_says_each_tools_tier_as_the_machine_check_has_it(
    tmp_path: Path,
) -> None:
    stage = Stage(tmp_path)
    for program in ("agtermctl", "claude", "codex"):
        stage.tool(program)
    look = stage.look()
    listed = []
    links = {}
    for title, section in tool_groups(text_of("install.md")).items():
        for line in section.splitlines():
            if line.startswith("- "):
                entry = re.match(r"- \[([^\]]+)\]\(([^)]+)\)", line)
                assert entry is not None, line
                label, link = entry.groups()
                name = ROW_NAMES.get(label.strip("`"), label)
                listed.append((name, title.lower()))
                links[name] = link

    rows = [row for part in TOOL_PARTS for row in guarded(part, look)]
    rows = [row for row in rows if row.name not in WITH_LEM]
    assert sorted(listed) == sorted((row.name, row.need) for row in rows)
    for row in rows:
        if row.guide:
            assert links[row.name] == row.guide, row.name


def test_the_install_guide_gives_the_brew_lines_of_a_machine_with_none_of_the_programs(
    tmp_path: Path,
) -> None:
    bare = reported(gathered(Stage(tmp_path).look()))
    needs = (
        text_of("install.md").split("## What you need\n", 1)[1].split("\n### ", 1)[0]
    )
    blocks = re.findall(r"```bash\n(.*?)```", needs, flags=re.DOTALL)
    assert [line for block in blocks for line in block.splitlines()] == list(bare.brew)

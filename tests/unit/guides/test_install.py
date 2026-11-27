"""The install guide has the same groups and recipe links as the doctor."""

import re
from typing import TYPE_CHECKING

from lem.cli.doctor.rows import guarded
from lem.cli.doctor.tool_parts import TOOL_PARTS
from unit.guides.test_guides import text_of
from unit.settings.doctor.stage import Stage

if TYPE_CHECKING:
    from pathlib import Path

ROW_NAMES = {
    "Claude Code": "claude",
    "Codex": "codex",
    "Python 3.14": "python3",
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
    assert sorted(listed) == sorted((row.name, row.need) for row in rows)
    for row in rows:
        if row.guide:
            assert links[row.name] == row.guide, row.name

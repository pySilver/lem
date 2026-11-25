"""`docs/settings.md` says what the structs hold: one row for each key of each file, each
default as the struct has it, and the files where each table is valid as `places.py` has
them."""

import re
import tomllib
from pathlib import Path

import msgspec
import pytest

from lem.settings import described, places
from lem.settings.machine import Machine
from lem.settings.personal import Home, Local
from lem.settings.places import Scope
from lem.settings.team import Team

PAGE = Path(__file__).resolve().parents[3] / "docs" / "settings.md"
# A row of a table of settings: its keys in backticks, its default, and its use.
ROW = re.compile(
    r"^\| (`[a-z_]+\.[A-Za-z_]+`(?:, `[a-z_]+\.[A-Za-z_]+`)*) \| ([^|]+) \|",
    re.MULTILINE,
)
KEY = re.compile(r"`([a-z_]+\.[A-Za-z_]+)`")
# The heading of each file's part of the page.
PARTS = (
    (Team, "## `.lem/settings.toml`"),
    (Local, "## `.lem/settings.local.toml`"),
    (Home, "## `~/.config/lem/settings.toml`"),
    (Machine, "## `~/.config/lem/machine.toml`"),
)
COLUMNS = (Scope.machine, Scope.home, Scope.team, Scope.local)


def part(heading: str) -> str:
    """The text of the page under `heading`, to the next heading of its level."""
    text = PAGE.read_text(encoding="utf-8")
    start = text.index(heading) + len(heading)
    end = text.find("\n## ", start)
    return text[start : end if end > 0 else None]


def keys_of(shape: type) -> set[str]:
    """Every `table.key` of a file's struct; `peers.HOST` for a table with no fixed keys."""
    found = set()
    for field in msgspec.structs.fields(shape):
        keys = described.keys_of(shape, field.name)
        found |= {f"{field.name}.{key}" for key in keys} or {f"{field.name}.HOST"}
    return found


def rows(heading: str) -> dict[str, str]:
    """Each key the part names, with the default its row gives."""
    return {
        key: default.strip()
        for keys, default in ROW.findall(part(heading))
        for key in KEY.findall(keys)
    }


@pytest.mark.parametrize(("shape", "heading"), PARTS, ids=[name for _, name in PARTS])
def test_each_file_has_a_row_for_each_key_of_its_struct(
    shape: type, heading: str
) -> None:
    named = set(rows(heading))
    tables = part(heading)
    if shape is Local:
        named = {
            f"{table}.{key}"
            for table in ("seats", "naps", "state")
            for key in described.keys_of(Local, table)
        }
        assert all(f"`[{table}]`" in tables for table in ("seats", "naps", "state"))
    assert named == keys_of(shape)


@pytest.mark.parametrize(
    ("shape", "heading"), PARTS[:1] + PARTS[2:], ids=["team", "home", "machine"]
)
def test_each_default_the_page_gives_is_the_structs(shape: type, heading: str) -> None:
    defaults = msgspec.json.decode(msgspec.json.encode(shape()))
    for key, default in rows(heading).items():
        table, name = key.split(".")
        written = re.fullmatch(r"`([^`]+)`", default)
        if not written or table not in defaults or name not in defaults[table]:
            continue
        given = tomllib.loads(f"value = {written[1]}")["value"]
        assert given == defaults[table][name], key


def test_the_page_says_where_each_table_is_valid_as_the_places_do() -> None:
    table = part("## Where each table is valid")
    found = {}
    for line in table.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(COLUMNS) + 1 or not cells[0].startswith("`["):
            continue
        valid = tuple(
            scope
            for scope, cell in zip(COLUMNS, cells[1:], strict=True)
            if cell != "no"
        )
        found |= dict.fromkeys(re.findall(r"`\[([a-z]+)\]`", cells[0]), valid)
    assert found == {
        name: tuple(scope for scope in COLUMNS if scope in valid)
        for name, valid in places.TABLES
    }


def test_no_text_of_lem_names_project_toml() -> None:
    root = PAGE.parents[1]
    texts = [*root.glob("skills/**/*.md"), *root.glob("docs/*.md"), root / "README.md"]
    named = [
        str(path)
        for path in texts
        if re.search(r"project(\.local)?\.toml", path.read_text(encoding="utf-8"))
    ]
    assert named == []

"""The read of the backlog from a main checkout: each item with its head, its worth, whether
its place in the code is still there and what git says of it, and an item that cannot be read
listed as such; git's answers come in through a stand-in of the `Ledger` it reads."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lem.board.views.backlog import head, ledger
from lem.board.views.backlog.ledger import Adding
from lem.board.views.backlog.read import read, where_problem
from lem.board.views.backlog_read import AddedBy
from lem.board.views.world import Place

if TYPE_CHECKING:
    from pathlib import Path

NOW = datetime(2026, 11, 25, 16, 0, tzinfo=UTC)
PLACE = Place(repo="shop", base="main", path="/work/shop")
FOLDER = "docs/backlog"


class Ledger:
    """Git's answers: the commits that added files, and the paths it does not have."""

    def __init__(
        self,
        adds: tuple[Adding, ...] | None = (),
        unsaved: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.added = adds
        self.left = unsaved

    def adds(self, where: Path, folder: str) -> tuple[Adding, ...] | None:
        return self.added

    def unsaved(self, where: Path, folder: str) -> tuple[tuple[str, str], ...] | None:
        return self.left


def item(checkout: Path, stem: str, head_lines: tuple[str, ...], text: str) -> str:
    """Write the item `stem` of the backlog folder; give its path."""
    path = f"{FOLDER}/{stem}.md"
    body = "\n".join(("---", *head_lines, "---", text, ""))
    (checkout / path).write_text(body, encoding="utf-8")
    return path


def test_the_board_s_backlog_has_each_item_with_its_worth_its_place_and_what_git_says(
    tmp_path: Path,
) -> None:
    """`main`'s `tests/lem-settings.sh` check "the board's backlog has each item with its
    worth, whether its place in the code is still there and whether git has it, and an item
    that cannot be read is listed as such"."""
    checkout = tmp_path
    (checkout / FOLDER).mkdir(parents=True)
    (checkout / "app").mkdir()
    (checkout / "app/export.py").write_text("def export_rows():\n    return []\n")
    export = item(
        checkout,
        "export-drops-columns",
        ("worth: yes", "where: app/export.py:export_rows", "added: 2026-11-02"),
        "# The export drops `custom` columns\n\nA merchant does not find the gift note.",
    )
    item(
        checkout,
        "slow-report",
        ("worth: later", "where: app/report.py:monthly", "added: 2026-10-20"),
        "# The monthly report takes nine seconds",
    )
    item(
        checkout,
        "which-currency",
        ("worth: yes", "where: app/export.py:no_such_name"),
        "# Which currency rounds half up",
    )
    item(checkout, "dark-theme", ("worth: no",), "# A dark theme\n\nDecided against.")
    fresh = item(
        checkout,
        "new-from-a-landing",
        ("worth: maybe", "where: app/export.py"),
        "# A new item",
    )
    (checkout / FOLDER / "a b;c.md").write_text("")
    (checkout / FOLDER / "broken-link.md").symlink_to("moved-away.md")
    (checkout / FOLDER / "folder-item.md").mkdir()
    (checkout / FOLDER / ".md").write_text("# no item\n")
    adding = Adding(author="t", day="2026-11-24", subject="start", paths=(export,))
    shelved = read(checkout, PLACE, Ledger((adding,), (("??", fresh),)), NOW)
    by = {entry.key: entry for entry in shelved.entries}
    assert (shelved.folder, shelved.reviewer, shelved.told, shelved.read) == (
        FOLDER,
        ".lem/state/backlog",
        True,
        NOW,
    )
    assert sorted(by) == [
        "a b;c",
        "broken-link",
        "dark-theme",
        "export-drops-columns",
        "folder-item",
        "new-from-a-landing",
        "slow-report",
        "which-currency",
    ]
    columns = by["export-drops-columns"]
    assert (columns.title, columns.worth, columns.where_problem, columns.path) == (
        "The export drops custom columns",
        "yes",
        None,
        export,
    )
    assert (columns.added_on, columns.text, columns.tracked) == (
        "2026-11-02",
        "A merchant does not find the gift note.",
        True,
    )
    assert columns.added == AddedBy(author="t", day="2026-11-24")
    assert by["slow-report"].where_problem == "the file is not there"
    assert by["which-currency"].where_problem == "not in the file: no_such_name"
    assert (by["dark-theme"].worth, by["dark-theme"].where) == ("no", None)
    new = by["new-from-a-landing"]
    assert (new.worth, new.tracked, new.added) == ("maybe", False, None)
    assert by["a b;c"].title == "a b;c"
    assert by["broken-link"].bad == "No such file or directory"
    assert by["folder-item"].bad == "Is a directory"


def test_the_first_item_of_a_backlog_folder_that_git_does_not_know_yet_is_new(
    tmp_path: Path,
) -> None:
    """`main`'s `tests/lem-settings.sh` check "the first item of a backlog folder that git
    does not know yet is new": git lists it file by file (`Ledger.unsaved`), and the read
    takes it as an item git has no commit of."""
    (tmp_path / FOLDER).mkdir(parents=True)
    (tmp_path / FOLDER / "first.md").write_text(
        "# The first item\n\nNo frontmatter at all.\n"
    )
    git = Ledger((), (("??", f"{FOLDER}/first.md"),))
    (first,) = read(tmp_path, PLACE, git, NOW).entries
    assert (first.tracked, first.title, first.worth) == (False, "The first item", None)


def test_the_reviewer_s_items_are_keyed_apart_and_git_is_never_asked_of_them(
    tmp_path: Path,
) -> None:
    reviewer = tmp_path / ".lem/state/backlog"
    reviewer.mkdir(parents=True)
    (tmp_path / FOLDER).mkdir(parents=True)
    for folder in (reviewer, tmp_path / FOLDER):
        (folder / "same.md").write_text("---\nworth: later\n---\n# Same\n")
    shelved = read(tmp_path, PLACE, Ledger(None), NOW)
    assert [(entry.key, entry.reviewer) for entry in shelved.entries] == [
        ("same", False),
        ("-same", True),
    ]
    assert not shelved.told


def test_a_head_that_is_not_yaml_is_an_item_that_says_why(tmp_path: Path) -> None:
    (tmp_path / FOLDER).mkdir(parents=True)
    (tmp_path / FOLDER / "odd.md").write_text("---\nworth: [later\n---\n# Odd\n")
    (odd,) = read(tmp_path, PLACE, None, NOW).entries
    assert odd.title == "odd"
    assert odd.bad and odd.bad.startswith("its head is not YAML")


def test_a_head_s_truth_values_and_days_are_the_words_written() -> None:
    parsed = head.parse(
        "---\nworth: no\nadded: 2026-11-25\n---\nText.\n# Title\nMore.\n"
    )
    assert isinstance(parsed, head.Head)
    assert (parsed.worth, parsed.added, parsed.title) == ("no", "2026-11-25", "Title")
    assert parsed.text == "Text.\n\nMore."


def test_an_item_title_comes_from_its_heading_after_front_matter() -> None:
    prefixed = "---\nworth: later\n---\n"
    titled = head.parse(f"{prefixed}# Keep `total` in the export\n\nDetails.")
    assert isinstance(titled, head.Head)
    assert titled.title == "Keep total in the export"
    assert titled.text == "Details."
    untitled = head.parse(f"{prefixed}## Details\n\nKeep the total.")
    assert isinstance(untitled, head.Head)
    assert untitled.title == ""


def test_a_place_outside_the_checkout_or_a_heading_missing_does_not_resolve(
    tmp_path: Path,
) -> None:
    (tmp_path / "AGENTS.md").write_text("# The shop\n\n## Checks\n")
    assert (
        where_problem(tmp_path, "../elsewhere.py") == "the path leaves the repository"
    )
    assert where_problem(tmp_path, "AGENTS.md:## Checks") is None
    assert (
        where_problem(tmp_path, "AGENTS.md:## Release")
        == "the heading is not in the file"
    )
    assert where_problem(tmp_path, "AGENTS.md") is None


def test_the_commit_that_added_an_item_names_its_task_or_its_pull_request() -> None:
    """`main`'s `board.added_by`: Lem's squash line, then the filing commit's subject, else the
    pull request its subject ends with; the newest commit that added a file wins, and a file
    under a folder of the backlog is no item."""
    squash = Adding(
        author="Ann",
        day="2026-11-24",
        subject="feat: the login (#41)",
        body="Lem task: fix-the-login\n",
        paths=(f"{FOLDER}/a.md",),
    )
    filing = Adding(
        author="Lem",
        day="2026-11-23",
        subject="docs(backlog): what review round 2 saw outside coupon-has-a-slug",
        paths=(f"{FOLDER}/b.md", f"{FOLDER}/a.md"),
    )
    merged = Adding(
        author="Bo",
        day="2026-11-22",
        subject="docs: two notes (#38)",
        paths=(f"{FOLDER}/c.md", f"{FOLDER}/old/d.md"),
    )
    assert ledger.added_by((squash, filing, merged), FOLDER) == {
        f"{FOLDER}/a.md": AddedBy(author="Ann", day="2026-11-24", task="fix-the-login"),
        f"{FOLDER}/b.md": AddedBy(
            author="Lem", day="2026-11-23", task="coupon-has-a-slug"
        ),
        f"{FOLDER}/c.md": AddedBy(author="Bo", day="2026-11-22", pull="38"),
    }


def test_git_s_two_letters_tell_a_new_item_from_an_edited_one() -> None:
    new, edited = ledger.changes((("??", "a.md"), ("A ", "b.md"), (" M", "c.md")))
    assert (new, edited) == (frozenset(("a.md", "b.md")), frozenset(("c.md",)))

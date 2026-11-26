"""The guides of docs/ as the one source of the site, and README.md as the pointer to it: each
guide in the nav, short, in sentences of STE length, with no old-form mark and no report of what
ran; each picture with its dark source and a caption that says what it shows; the site's tools
pinned and its publishing started by hand only."""

import re
import subprocess
import tomllib
from pathlib import Path

from unit.cli import reading

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
CONFIG = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
NAV = [next(iter(entry.values())) for entry in CONFIG["project"]["nav"]]
# docs/settings.md is the settings step's reference, one to one with the settings' structs
# (tests/unit/settings/test_docs.py), and it may be longer; the home page holds the sections of a
# landing page.
GUIDES = [name for name in NAV if name not in {"settings.md", "index.md"}]
# The owner's ruling: "A guide of `docs/` aims at under 800 words, or a bit more when needed."
WORDS = 800
# A landing page of 800 to 1600 words of visible text, as the hand-kept page had.
HOME_WORDS = 1600
# ASD-STE100: 25 words at most in a descriptive sentence.
SENTENCE = 25
# The maintainer's files of docs/ that stay off the site.
OFF_SITE = {"plans", "backlog", "rulings", "free-hour.md"}
SITE = "https://pysilver.github.io/lem/"
INSTALL = (
    "brew install pySilver/tap/lem",
    "claude plugin marketplace add pySilver/lem --scope project",
    "claude plugin install lem@lem --scope project",
)
# Words that report a run, or name an operating system, which the README and the docs leave out.
REPORTS = re.compile(r"\b(proven|not run yet|was tested|we measured)\b", re.IGNORECASE)
SYSTEMS = re.compile(r"\b(macOS|Linux|Windows)\b")


def text_of(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def prose(text: str) -> str:
    """The words a reader reads: no front matter, code block, tag, link target or table."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"^```.*?^```", "", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    return re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)


def words(text: str) -> int:
    return len([word for word in text.split() if re.search(r"[A-Za-z0-9]", word)])


def sentences(text: str) -> list[str]:
    """The sentences of each paragraph and list item of the prose."""
    found = []
    blocks = re.split(r"\n\s*\n|\n(?=\s*(?:[-*]|\d+\.)\s)|\n(?=#)", prose(text))
    for block in blocks:
        joined = re.sub(r"^(?:[-*]|\d+\.)\s+", "", " ".join(block.split()))
        joined = re.sub(r"^\*\*[^*]+\*\*\s*", "", joined)
        found += re.split(r"(?<=[.!?:;])\s+(?=[A-Z`\"*\[(/])", joined)
    return [sentence for sentence in found if sentence]


def test_each_page_of_the_nav_is_a_file_of_docs_and_each_page_of_docs_is_in_the_nav() -> (
    None
):
    assert NAV[0] == "index.md"
    for name in NAV:
        assert (DOCS / name).is_file(), name
    pages = {path.name for path in DOCS.glob("*.md")} - OFF_SITE
    assert pages == set(NAV)


def test_the_site_leaves_out_the_maintainers_files_of_docs_and_those_are_there() -> (
    None
):
    left_out = {line.strip("/") for line in CONFIG["project"]["exclude_docs"].split()}
    assert left_out == OFF_SITE
    for name in OFF_SITE:
        assert (DOCS / name).exists(), name


def test_the_site_is_built_into_site_with_no_web_font_and_no_switch_of_the_theme() -> (
    None
):
    project = CONFIG["project"]
    assert project["site_dir"] == "_site"
    assert project["docs_dir"] == "docs"
    assert project["theme"]["font"] is False
    assert all("toggle" not in palette for palette in project["theme"]["palette"])
    assert "content.action.copy" in project["theme"]["features"]
    assert (
        set(project["plugins"]["llmstxt"]["sections"]) and project["plugins"]["llmstxt"]
    )


def test_each_guide_aims_at_under_800_words_and_the_home_page_at_1600() -> None:
    counts = {name: words(prose(text_of(name))) for name in GUIDES}
    assert {name: count for name, count in counts.items() if count >= WORDS} == {}
    assert words(prose(text_of("index.md"))) <= HOME_WORDS


def test_no_sentence_of_a_guide_or_the_readme_has_more_than_25_words() -> None:
    texts = {name: text_of(name) for name in [*GUIDES, "index.md"]}
    texts["README.md"] = (ROOT / "README.md").read_text(encoding="utf-8")
    long = [
        (name, sentence[:80])
        for name, text in texts.items()
        for sentence in sentences(text)
        if words(sentence) > SENTENCE
    ]
    assert long == []


def test_no_guide_carries_the_old_form_mark_or_reports_what_ran() -> None:
    for name in [*NAV, "../README.md"]:
        text = (DOCS / name).read_text(encoding="utf-8")
        assert not reading.marked(text), name
        assert not REPORTS.search(prose(text)), name


def test_the_readme_and_the_home_page_name_no_operating_system_and_no_plannotator() -> (
    None
):
    for path in (ROOT / "README.md", DOCS / "index.md"):
        text = path.read_text(encoding="utf-8")
        assert not SYSTEMS.search(prose(text)), path
        assert "plannotator" not in text.lower(), path


def test_the_readme_points_to_the_site_and_installs_as_the_home_page_does() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    home = text_of("index.md")
    assert f"]({SITE})" in readme
    for line in INSTALL:
        assert f"\n{line}\n" in readme, line
        assert f"\n{line}\n" in home, line
    assert "a plugin for Claude Code that works closely with" in readme
    assert "works closely with agterm" in home
    assert (
        "For a developer who works alone, and for a team on Linear or GitHub Issues."
        in readme
    )
    assert (
        "For a developer who works alone, and for a team on Linear or GitHub Issues."
        in home
    )
    assert readme.rstrip().endswith("Lem has the [MIT License](LICENSE).")
    for link in re.findall(rf"\]\({re.escape(SITE)}([^)]*)\)", readme):
        page = link.strip("/")
        assert not page or (DOCS / f"{page}.md").is_file(), link


def test_each_picture_has_its_dark_source_and_a_caption_that_says_demo_data() -> None:
    for name in NAV:
        text = text_of(name)
        for light in re.findall(r'<img src="([^"]*-light\.png)"', text):
            dark = light.replace("-light.png", "-dark.png")
            assert f'srcset="{dark}"' in text, (name, light)
            after = text.split(light, 1)[1].split("</picture>", 1)[1].lstrip()
            assert after.startswith("*") and "demo data" in after.split("\n", 1)[0], (
                name
            )


def test_each_example_dialog_says_it_is_an_illustration() -> None:
    home = text_of("index.md")
    dialogs = re.findall(r"```text\n(you .*?)```", home, flags=re.DOTALL)
    assert dialogs
    before = home.split("```text", 1)[0].strip().rsplit("\n\n", 1)[-1]
    assert "illustrations, not the output of a run" in before


def test_zensical_is_pinned_to_one_exact_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pins = [
        dep for dep in project["dependency-groups"]["dev"] if dep.startswith("zensical")
    ]
    assert len(pins) == 1
    assert re.fullmatch(r"zensical==\d+\.\d+\.\d+", pins[0]), pins[0]
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    version = pins[0].split("==")[1]
    assert f'name = "zensical"\nversion = "{version}"' in lock


def test_pages_yml_builds_with_zensical_and_publishes_only_on_a_start_by_hand() -> None:
    text = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    on = text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert on.strip() == "workflow_dispatch:"
    for line in (
        "pages: write",
        "id-token: write",
        "name: github-pages",
        "actions/configure-pages@",
        "actions/upload-pages-artifact@",
        "actions/deploy-pages@",
        "uv sync --locked",
        ".venv/bin/zensical build --clean --strict",
        "path: _site",
    ):
        assert line in text, line


def test_git_tracks_no_hand_kept_page() -> None:
    ran = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "site"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert ran.stdout == ""

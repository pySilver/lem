"""The two first pages of the site. The landing page at its root, landing/index.html by hand: the
scene, the opening, the install lines of the install guide, the way into each page of the docs and
no guide text of its own. The docs' first page, built from docs/index.md: the sections a visitor
reads in order. Both in the board's hues."""

import json
import re
import shutil
import struct
import subprocess
import tomllib
from html import unescape
from pathlib import Path

import pytest

from unit.guides import built

ROOT = built.ROOT
INSTALL = (
    "brew install pySilver/tap/lem",
    "claude plugin marketplace add pySilver/lem --scope project",
    "claude plugin install lem@lem --scope project",
)
LEAD = "Type a request in plain words, and get a pull request whose first line says green or not green."
FOR = "For a developer who works alone, and for a team on Linear or GitHub Issues."
SECTIONS = [
    "How a task goes",
    "What you can rely on",
    "The board, also on your phone",
    "Start from a ticket",
    "Lem learns your repository",
    "What you type",
]
HUES = ("--lead", "--lem", "--you", "--bad", "--gate", "--ok")
# The visible text of the docs' first page, as the hand-kept landing page had it before 2026-11-26.
HOME_WORDS = (800, 1600)
SITE_CSS = ROOT / "docs/assets/lem-site.css"
LANDING_CSS = ROOT / "landing/style.css"
# The landing page holds the pitch, the install and the names of the guides: 190 words on
# 2026-11-27. One paragraph of a guide on it would take it over this bound.
LANDING_WORDS = 220
CONFIG = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
NAV = [next(iter(entry.values())) for entry in CONFIG["project"]["nav"]]


def home(site: Path) -> str:
    return (site / "index.html").read_text(encoding="utf-8")


def article(site: Path) -> str:
    """The visible words of the docs' first page, with no tag."""
    text = home(site).split('<article class="md-content__inner md-typeset">', 1)[1]
    text = text.split("</article>", 1)[0]
    text = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", text, flags=re.DOTALL)
    text = re.sub(r'<a class="headerlink"[^>]*>.*?</a>', "", text)
    text = re.sub(r"</?(?:a|code|b|strong|em|span)\b[^>]*>", "", text)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", text)).split())


def visible(page: str) -> str:
    """The visible words of a page's body, with no tag, script or style."""
    text = page.split("<body", 1)[1]
    text = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", text, flags=re.DOTALL)
    text = re.sub(r"</?(?:a|code|b|strong|em|span)\b[^>]*>", "", text)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", text)).split())


def install_lines_of_the_guide() -> list[str]:
    """The lines of the bash blocks of the section "Install" of docs/install.md."""
    text = (ROOT / "docs/install.md").read_text(encoding="utf-8")
    section = text.split("\n## Install\n", 1)[1].split("\n## ", 1)[0]
    blocks = re.findall(r"```bash\n(.*?)```", section, flags=re.DOTALL)
    return [line for block in blocks for line in block.splitlines() if line.strip()]


def test_the_scene_stands_over_the_page_in_its_day_and_its_night_file(
    landing: Path,
) -> None:
    page = home(landing)
    scene = page.split('<div class="scene">', 1)[1].split("</div>", 1)[0]
    assert (
        '<source media="(prefers-color-scheme: dark)" srcset="docs/assets/lem-night.svg">'
        in scene
    )
    assert '<img src="docs/assets/lem.svg"' in scene
    assert LEAD not in scene, "the words stand on the page, under the scene"
    css = LANDING_CSS.read_text(encoding="utf-8")
    assert "--scene: max(40vw, min(260px, 60vw));" in css
    rule = css.split(".scene img {", 1)[1].split("}", 1)[0]
    for part in ("object-fit: cover", "object-position: 50% 0", "var(--scene)"):
        assert part in rule, part


def test_the_opening_has_the_lead_who_lem_is_for_the_install_lines_and_agterm(
    landing: Path,
) -> None:
    words = visible(home(landing))
    assert words.index(LEAD) < words.index(FOR) < words.index(INSTALL[0])
    assert "Lem is a plugin for Claude Code that works closely with agterm." in words
    assert "Lem needs agterm." in words
    for line in INSTALL:
        assert line in words, line


def test_the_landing_pages_install_lines_are_those_of_the_install_guide(
    landing: Path,
) -> None:
    page = home(landing)
    lines = re.findall(
        r'<div class="cmd"><code>([^<]*)</code><button class="copy" type="button">Copy</button></div>',
        page,
    )
    assert lines == install_lines_of_the_guide()
    assert lines == list(INSTALL)


def test_the_landing_page_links_each_page_of_the_docs_and_holds_no_guide_text(
    landing: Path,
) -> None:
    links = {
        tag.attributes["href"]
        for tag in built.read(landing / "index.html").tags
        if tag.name == "a" and "href" in tag.attributes
    }
    docs = {link for link in links if link.startswith("docs/")}
    assert docs == {
        "docs/" if name == "index.md" else f"docs/{name.removesuffix('.md')}/"
        for name in NAV
    }
    for link in docs:
        assert (landing / link / "index.html").is_file(), link
    count = len(
        [word for word in visible(home(landing)).split() if re.search(r"\w", word)]
    )
    assert count <= LANDING_WORDS, count


def test_the_landing_page_loads_its_own_files_only_and_its_one_script_copies(
    landing: Path,
) -> None:
    page = home(landing)
    for tag in built.read(landing / "index.html").tags:
        named = [
            tag.attributes[name]
            for name in ("src", "srcset", "href")
            if name in tag.attributes and tag.name in {"img", "source", "link"}
        ]
        for name in named:
            assert (landing / name).is_file(), tag.attributes
        assert not (tag.name == "script" and "src" in tag.attributes), tag.attributes
    [script] = re.findall(r"<script>(.*?)</script>", page, flags=re.DOTALL)
    assert 'document.querySelectorAll("button.copy")' in script
    assert "fetch" not in script
    assert "//" not in re.sub(
        r"/\*.*?\*/", "", LANDING_CSS.read_text(encoding="utf-8"), flags=re.DOTALL
    )


def test_the_desktop_scene_reserves_room_for_install_on_the_first_screen(
    landing: Path,
) -> None:
    css = (landing / "style.css").read_text(encoding="utf-8")
    desktop = re.search(
        r"@media \(min-width: 1000px\)\s*\{\s*\.scene img\s*\{\s*"
        r"max-height: max\((\d+)vw, (\d+)vh\)",
        css,
    )
    assert desktop is not None, "the desktop scene needs a viewport height limit"
    # At the ledger's 1280 × 800, reserve 440 px for the bar, the text and the install block.
    assert max(1280 * int(desktop[1]), 800 * int(desktop[2])) / 100 <= 360


def test_the_install_button_copies_the_commands(site: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("no node on PATH to run the built site's JavaScript")
    page = home(site)
    reader = built.read(site / "index.html")
    [(kind, block)] = [
        block for block in reader.blocks if block[1].startswith(INSTALL[0])
    ]
    assert block.splitlines() == list(INSTALL)
    [pre] = [
        tag.attributes
        for tag in reader.tags
        if tag.name == "pre" and "lem-chart" not in tag.attributes.get("class", "")
    ][:1]
    [source] = [
        tag.attributes["src"]
        for tag in reader.tags
        if tag.name == "script" and "/bundle." in tag.attributes.get("src", "")
    ]
    config = re.search(r'<script id="__config"[^>]*>(.*?)</script>', page)
    assert config is not None
    ran = subprocess.run(
        [node, str(ROOT / "tests/unit/guides/copy.mjs"), str(site / source)],
        input=json.dumps(
            {
                "config": config[1],
                "block": block,
                "highlightClass": kind,
                "preAttributes": pre,
            }
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ran.returncode == 0, ran.stderr


def test_the_sections_stand_in_order_and_say_what_the_landing_page_said(
    site: Path,
) -> None:
    page = home(site)
    found = [
        unescape(re.sub(r"<[^>]+>", "", heading)).rstrip("¶")
        for heading in re.findall(r"<h2[^>]*>(.*?)</h2>", page)
    ]
    assert found == SECTIONS
    words = article(site)
    for sentence in (
        "Nothing merges before your tests pass and an agent that did not build the change reviews it.",
        "A step that nobody can undo stops the task, and waits for you.",
        "Lem never pushes over a commit that it did not push.",
        "Green usually lets you merge without your own read.",
        "/lem new ABC-12",
        "/lem new 42",
        "Each developer has their own board, with the tasks on their own computer.",
        ".lem/profile.md",
        ".lem/personas/",
        ".lem/lessons.md",
        "docs/rulings.md",
        "a second model family reviews the larger changes",
        "MIT License",
    ):
        assert sentence in words, sentence


def test_the_home_page_has_800_to_1600_words_of_visible_text(site: Path) -> None:
    count = len(
        [word for word in article(site).split() if re.search(r"[A-Za-z0-9]", word)]
    )
    assert HOME_WORDS[0] <= count <= HOME_WORDS[1], count


def test_the_tab_icon_is_the_figure_alone_by_day_and_by_night(
    site: Path, landing: Path
) -> None:
    for page, assets in ((site, "./assets/"), (landing, "docs/assets/")):
        icons = re.findall(r'<link rel="icon"[^>]*>', home(page))
        assert len(icons) == 3
        assert f'href="{assets}lem-mark.svg"' in icons[0] and "media" not in icons[0]
        assert (
            f'href="{assets}lem-mark-night.svg"' in icons[1]
            and "(prefers-color-scheme: dark)" in icons[1]
        )
        assert (
            f'href="{assets}lem-mark.svg"' in icons[2]
            and "(prefers-color-scheme: light)" in icons[2]
        )


def png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def test_each_picture_of_the_board_says_its_size_as_half_the_pixels_of_its_files(
    landing: Path,
) -> None:
    pictures = 0
    for page in built.pages(landing):
        for tag in built.read(page).tags:
            source = tag.attributes.get("src", "")
            if tag.name != "img" or "/screens/" not in source:
                continue
            pictures += 1
            for theme in ("light", "dark"):
                file = (
                    ROOT
                    / "assets/screens"
                    / Path(source).name.replace("-light", f"-{theme}")
                )
                width, height = png_size(file)
                assert (tag.attributes["width"], tag.attributes["height"]) == (
                    str(width // 2),
                    str(height // 2),
                ), (page, source, theme)
    assert pictures >= 3


def test_the_sites_style_has_the_six_hues_and_the_palettes_of_lem_css() -> None:
    lem_css = (ROOT / "skills/lem/assets/lem.css").read_text(encoding="utf-8")
    allowed = set(re.findall(r"#[0-9a-f]{6}", lem_css))
    for path in (SITE_CSS, LANDING_CSS):
        site_css = path.read_text(encoding="utf-8")
        for hue in HUES:
            value = re.search(rf"{hue}:\s*(#[0-9a-f]{{6}})", lem_css)
            assert value is not None, hue
            assert f"{hue}: {value[1]};" in site_css, (path, hue)
        assert set(re.findall(r"#[0-9a-f]{3,8}\b", site_css)) <= allowed, path


def test_the_light_and_the_dark_palette_differ_and_each_gives_pele_its_colors() -> None:
    landing = LANDING_CSS.read_text(encoding="utf-8")
    light_root = landing.split(":root {", 1)[1].split("}", 1)[0]
    dark_root = landing.split("@media (prefers-color-scheme: dark)", 1)[1]
    dark_root = dark_root.split("}", 1)[0]
    landing_bg = re.compile(r"--bg:\s*(#[0-9a-f]{6})")
    light_bg, dark_bg = landing_bg.search(light_root), landing_bg.search(dark_root)
    assert light_bg is not None and dark_bg is not None
    assert light_bg[1] != dark_bg[1]
    css = SITE_CSS.read_text(encoding="utf-8")
    light = css.split('[data-md-color-scheme="default"] {', 1)[1].split("}", 1)[0]
    dark = css.split('[data-md-color-scheme="slate"] {', 1)[1].split("}", 1)[0]
    background = re.compile(r"--lem-bg:\s*(#[0-9a-f]{6})")
    light_bg, dark_bg = background.search(light), background.search(dark)
    assert light_bg is not None and dark_bg is not None
    assert light_bg[1] != dark_bg[1]
    both = css.split(
        '[data-md-color-scheme="default"], [data-md-color-scheme="slate"] {', 1
    )[1]
    both = both.split("}", 1)[0]
    pele = (ROOT / "skills/lem/assets/vendor/pele.js").read_text(encoding="utf-8")
    read = set(
        re.findall(
            r"var\((--pele-(?:bg|fg|muted|line|surface|surface-alt|border))\b", pele
        )
    )
    assert read
    for variable in read:
        assert f"{variable}:" in both, variable


def test_the_pictures_of_the_theme_are_links_to_the_files_of_assets() -> None:
    for link in (ROOT / "docs/assets").rglob("*"):
        if link.suffix in {".png", ".svg"} or link.name == "pele.js":
            assert link.is_symlink(), link
            assert (
                link.resolve().is_relative_to(ROOT / "assets") or link.name == "pele.js"
            ), link

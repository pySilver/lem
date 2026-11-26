"""The home page of the site, as built from docs/index.md through overrides/home.html: the
scene, the opening, the sections a visitor reads in order, and the look in the board's hues."""

import json
import re
import shutil
import struct
import subprocess
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
# The visible text of a landing page, as the hand-kept page had it.
HOME_WORDS = (800, 1600)


def home(site: Path) -> str:
    return (site / "index.html").read_text(encoding="utf-8")


def article(site: Path) -> str:
    """The visible words of the home page's text, with no tag."""
    text = home(site).split('<article class="md-content__inner md-typeset">', 1)[1]
    text = text.split("</article>", 1)[0]
    text = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", text, flags=re.DOTALL)
    text = re.sub(r'<a class="headerlink"[^>]*>.*?</a>', "", text)
    text = re.sub(r"</?(?:a|code|b|strong|em|span)\b[^>]*>", "", text)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", text)).split())


def test_the_scene_stands_over_the_page_in_its_day_and_its_night_file(
    site: Path,
) -> None:
    page = home(site)
    scene = page.split('<div class="lem-scene">', 1)[1].split("</div>", 1)[0]
    assert (
        '<source media="(prefers-color-scheme: dark)" srcset="./assets/lem-night.svg">'
        in scene
    )
    assert '<img src="./assets/lem.svg"' in scene
    assert LEAD not in scene, "the words stand on the page, under the scene"
    css = (ROOT / "docs/assets/lem-site.css").read_text(encoding="utf-8")
    rule = css.split(".lem-scene img {", 1)[1].split("}", 1)[0]
    for part in (
        "object-fit: cover",
        "object-position: 50% 0",
        "max(40vw, min(260px, 60vw))",
    ):
        assert part in rule, part


def test_the_opening_has_the_lead_who_lem_is_for_the_install_lines_and_agterm(
    site: Path,
) -> None:
    words = article(site)
    assert words.index(LEAD) < words.index(FOR) < words.index(INSTALL[0])
    assert "Lem is a plugin for Claude Code that works closely with agterm." in words
    assert "Lem needs agterm." in words
    for line in INSTALL:
        assert line in words, line


def test_the_desktop_scene_reserves_room_for_install_on_the_first_screen(
    site: Path,
) -> None:
    css = (site / "assets/lem-site.css").read_text(encoding="utf-8")
    desktop = re.search(
        r"@media \(min-width: 960px\)\s*\{\s*\.lem-scene img\s*\{\s*"
        r"max-height: max\((\d+)vw, (\d+)vh\)",
        css,
    )
    assert desktop is not None, "the desktop scene needs a viewport height limit"
    # At the ledger's 1280 × 800, reserve 440 px for the header, text and install block.
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


def test_the_tab_icon_is_the_figure_alone_by_day_and_by_night(site: Path) -> None:
    icons = re.findall(r'<link rel="icon"[^>]*>', home(site))
    assert len(icons) == 3
    assert 'href="./assets/lem-mark.svg"' in icons[0] and "media" not in icons[0]
    assert (
        'href="./assets/lem-mark-night.svg"' in icons[1]
        and "(prefers-color-scheme: dark)" in icons[1]
    )
    assert (
        'href="./assets/lem-mark.svg"' in icons[2]
        and "(prefers-color-scheme: light)" in icons[2]
    )


def png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def test_each_picture_of_the_board_says_its_size_as_half_the_pixels_of_its_files(
    site: Path,
) -> None:
    pictures = 0
    for page in built.pages(site):
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
    site_css = (ROOT / "docs/assets/lem-site.css").read_text(encoding="utf-8")
    lem_css = (ROOT / "skills/lem/assets/lem.css").read_text(encoding="utf-8")
    for hue in HUES:
        value = re.search(rf"{hue}:\s*(#[0-9a-f]{{6}})", lem_css)
        assert value is not None, hue
        assert f"{hue}: {value[1]};" in site_css, hue
    allowed = set(re.findall(r"#[0-9a-f]{6}", lem_css))
    assert set(re.findall(r"#[0-9a-f]{3,8}\b", site_css)) <= allowed


def test_the_light_and_the_dark_palette_differ_and_each_gives_pele_its_colors() -> None:
    css = (ROOT / "docs/assets/lem-site.css").read_text(encoding="utf-8")
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

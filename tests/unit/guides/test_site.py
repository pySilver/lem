"""The built site: Zensical builds it from docs/ with no warning, and each page loads nothing
from another host, gives only `lem` lines the command tree takes, links only to what is there,
has its Markdown copy and the page menu, and draws each chart with Pele."""

import json
import re
import shutil
import subprocess
import tomllib
from typing import TYPE_CHECKING
from urllib.parse import unquote, urljoin, urlsplit

import pytest

from unit.cli import reading, shapes
from unit.guides import built

if TYPE_CHECKING:
    from pathlib import Path

TREE = shapes.tree()
CONFIG = tomllib.loads((built.ROOT / "zensical.toml").read_text(encoding="utf-8"))
SITE_URL = CONFIG["project"]["site_url"]
# The tags that make the browser fetch a file, with the attribute that names it.
FETCHED = (
    ("script", "src"),
    ("img", "src"),
    ("iframe", "src"),
    ("embed", "src"),
    ("video", "src"),
    ("audio", "src"),
    ("source", "src"),
    ("object", "data"),
)
# A <link> that makes the browser fetch its href; canonical, alternate, prev and next only name.
FETCHED_LINKS = {
    "stylesheet",
    "icon",
    "preload",
    "modulepreload",
    "preconnect",
    "dns-prefetch",
    "prefetch",
    "manifest",
    "apple-touch-icon",
}
OUTSIDE = re.compile(r"^(?:[a-z]+:)?//", re.IGNORECASE)
CSS_OUTSIDE = re.compile(
    r"(?:url\(\s*['\"]?|@import\s+['\"])(?:https?:)?//", re.IGNORECASE
)
# The pages a guide of zensical.toml's nav becomes, by the file it comes from.
NAV = [next(iter(entry.values())) for entry in CONFIG["project"]["nav"]]
# The Markdown copy of a page, and the assistants the page menu opens it in.
ASSISTANTS = (
    "https://chatgpt.com/?q=",
    "https://claude.ai/new?q=",
    "https://www.perplexity.ai/search?q=",
)
NODE_SECONDS = 60


def page_of(source: str) -> str:
    """The built page of a file of docs/: index.md is the home page, flow.md is flow/."""
    stem = source.removesuffix(".md")
    return "index.html" if stem == "index" else f"{stem}/index.html"


def fetched(tag: built.Tag) -> list[str]:
    """What one tag makes the browser fetch."""
    names = [
        tag.attributes.get(attribute, "")
        for name, attribute in FETCHED
        if tag.name == name
    ]
    if tag.name in {"img", "source"} and "srcset" in tag.attributes:
        names += [
            part.split()[0]
            for part in tag.attributes["srcset"].split(",")
            if part.strip()
        ]
    rels = set(tag.attributes.get("rel", "").lower().split())
    if tag.name == "link" and rels & FETCHED_LINKS:
        names.append(tag.attributes.get("href", ""))
    return [name for name in names if name]


def test_the_site_builds_with_no_warning(site_build: built.Build) -> None:
    assert site_build.code == 0, site_build.said
    assert "No issues found" in site_build.said, site_build.said


def test_each_guide_of_the_nav_is_a_page_and_no_maintainers_file_is(site: Path) -> None:
    for source in NAV:
        assert (site / page_of(source)).is_file(), source
    for gone in (
        "plans",
        "backlog",
        "rulings",
        "free-hour",
        "assets/eslint.config.mjs",
    ):
        assert not (site / gone).exists(), f"{gone} of docs/ is on the site"
    pages = {built.name_of(site, page) for page in built.pages(site)}
    assert pages == {page_of(source) for source in NAV} | {"404.html"}


def test_no_page_loads_a_thing_from_another_host(site: Path) -> None:
    found = []
    for page in built.pages(site):
        reader = built.read(page)
        for tag in reader.tags:
            if tag.attributes.get("data-md-component") == "source":
                found.append((built.name_of(site, page), "repository API widget"))
            found += [
                (built.name_of(site, page), name)
                for name in fetched(tag)
                if OUTSIDE.match(name)
            ]
            style = tag.attributes.get("style", "")
            if CSS_OUTSIDE.search(style):
                found.append((built.name_of(site, page), style))
        text = page.read_text(encoding="utf-8")
        found += [
            (built.name_of(site, page), "a <style> or @import")
            for _ in CSS_OUTSIDE.finditer(text)
        ]
    for sheet in site.rglob("*.css"):
        found += [
            (str(sheet.relative_to(site)), hit[0])
            for hit in CSS_OUTSIDE.finditer(sheet.read_text(encoding="utf-8"))
        ]
    assert found == []


def test_each_page_links_to_the_repository(site: Path) -> None:
    for page in built.pages(site):
        assert any(
            tag.name == "a"
            and tag.attributes.get("href") == "https://github.com/pySilver/lem"
            and tag.attributes.get("data-md-component") != "source"
            for tag in built.read(page).tags
        ), page


def test_no_page_loads_a_web_font_or_offers_a_switch_of_the_theme(site: Path) -> None:
    for page in built.pages(site):
        text = page.read_text(encoding="utf-8")
        assert "fonts.googleapis" not in text, page
        assert "fonts.gstatic" not in text, page
        assert 'for="__palette_' not in text, f"{page} has a switch of the theme"


def test_each_lem_line_of_the_site_is_one_the_tree_takes(site: Path) -> None:
    wrong = []
    lines = 0
    for page in built.pages(site):
        reader = built.read(page)
        name = built.name_of(site, page)
        calls = [
            reading.Line(name, 1, span.strip(), span=True)
            for span in reader.spans
            if reading.CALL.match(span.strip())
        ]
        for kind, block in reader.blocks:
            if not shell(kind):
                continue
            calls += [
                reading.Line(name, number, text.strip(), span=False)
                for number, text in enumerate(block.splitlines(), 1)
                if reading.CALL.match(text.strip())
            ]
        lines += len(calls)
        wrong += [
            f"{line.path}: {line.text}: {said}"
            for line in calls
            if (said := reading.verdict(line, TREE))
        ]
    assert wrong == []
    assert lines > 0, "the site gives no lem line to check"


def shell(kind: str) -> bool:
    """Whether a block of the page holds shell lines: a block marked bash, sh, shell, console
    or nothing, as the Markdown reader of tests/unit/cli takes them (a text block is a
    transcript, a chart is a chart)."""
    marks = re.findall(r"language-([\w+-]+)", kind)
    return "lem-chart" not in kind and all(mark in reading.SHELL for mark in marks)


def resolved(site: Path, page: Path, href: str) -> tuple[Path, str] | None:
    """The file and the heading a link of `page` names, or None for a link to another host or
    outside the published site."""
    root = urlsplit(SITE_URL)
    parts = urlsplit(urljoin(urljoin(SITE_URL, built.name_of(site, page)), href))
    if (parts.scheme, parts.netloc) != (root.scheme, root.netloc):
        return None
    path = unquote(parts.path)
    if path == root.path.rstrip("/"):
        path = root.path
    if not path.startswith(root.path):
        return None
    target = (site / path.removeprefix(root.path)).resolve()
    if target.is_dir() or parts.path.endswith("/"):
        target /= "index.html"
    return target, unquote(parts.fragment)


def test_absolute_links_to_the_site_resolve_to_local_files(site: Path) -> None:
    page = site / "404.html"
    assert resolved(site, page, SITE_URL) == (site / "index.html", "")
    assert resolved(site, page, SITE_URL + "flow/#careful") == (
        site / "flow/index.html",
        "careful",
    )
    assert resolved(site, page, SITE_URL + "missing/") == (
        site / "missing/index.html",
        "",
    )
    assert resolved(site, page, "https://agterm.com/") is None


def test_every_link_and_picture_of_the_site_names_a_file_and_a_heading_that_are_there(
    site: Path,
) -> None:
    ids = {page.resolve(): built.read(page).ids for page in built.pages(site)}
    broken = []
    for page in built.pages(site):
        for tag in built.read(page).tags:
            for name in [tag.attributes.get("href", ""), *fetched(tag)]:
                found = resolved(site, page, name) if name else None
                if found is None:
                    continue
                target, fragment = found
                if not target.is_file():
                    broken.append(f"{built.name_of(site, page)}: {name}")
                elif (
                    fragment
                    and target.suffix == ".html"
                    and fragment not in ids[target]
                ):
                    broken.append(
                        f"{built.name_of(site, page)}: {name} (no such heading)"
                    )
    assert broken == []


def test_llms_txt_lists_each_guide_and_each_markdown_copy_is_beside_its_page(
    site: Path,
) -> None:
    listed = re.findall(
        r"\]\(<([^>]+)>\)", (site / "llms.txt").read_text(encoding="utf-8")
    )
    pages = sorted(link.removeprefix(SITE_URL) for link in listed)
    assert pages == sorted(page_of(source).replace(".html", ".md") for source in NAV)
    for copy in pages:
        text = (site / copy).read_text(encoding="utf-8")
        assert text.startswith("# "), copy
        assert "<div" not in text, copy


def test_each_page_has_copy_as_markdown_and_the_page_menu(site: Path) -> None:
    for source in NAV:
        page = site / page_of(source)
        text = page.read_text(encoding="utf-8")
        markdown = page_of(source).replace(".html", ".md")
        assert 'data-md-copy-url="./index.md"' in text, source
        reader = built.read(page)
        links = [
            tag.attributes["href"]
            for tag in reader.tags
            if tag.name == "a" and "href" in tag.attributes
        ]
        assert "./index.md" in links, f"{source}: no View as Markdown"
        for assistant in ASSISTANTS:
            opened = [link for link in links if link.startswith(assistant)]
            assert len(opened) == 1, (source, assistant)
            assert SITE_URL.replace(":", "%3A") + markdown in opened[0], opened[0]
        assert ">View as Markdown</a>" in text, source


def charts(site: Path) -> list[tuple[str, str]]:
    """Each chart of the site: the page, and the text Pele reads."""
    return [
        (built.name_of(site, page), block)
        for page in built.pages(site)
        for kind, block in built.read(page).blocks
        if "lem-chart" in kind
    ]


def test_zensicals_mermaid_loader_finds_no_chart_and_each_chart_is_a_pre_lem_chart(
    site: Path,
) -> None:
    for page in built.pages(site):
        for tag in built.read(page).tags:
            assert "mermaid" not in tag.attributes.get("class", ""), page
    assert {page for page, _ in charts(site)} == {
        "index.html",
        "flow/index.html",
        "merge/index.html",
    }


def test_pele_draws_each_chart_of_the_site(site: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip(
            "no node on PATH: brew install node, which the ESLint gate needs too"
        )
    driver = built.ROOT / "tests/unit/guides/draw.mjs"
    chart_blocks = charts(site)
    for name in sorted({name for name, _ in chart_blocks}):
        page = site / name
        [source] = [
            tag.attributes["src"]
            for tag in built.read(page).tags
            if tag.name == "script"
            and tag.attributes.get("src", "").endswith("/lem-charts.js")
        ]
        target = resolved(site, page, source)
        assert target is not None, source
        script, _ = target
        ran = subprocess.run(
            [node, str(driver), str(site), script.relative_to(site).as_posix()],
            input=json.dumps([text for path, text in chart_blocks if path == name]),
            capture_output=True,
            text=True,
            check=False,
            timeout=NODE_SECONDS,
        )
        assert ran.returncode == 0, (name, ran.stderr)


def test_the_scripts_and_the_pictures_the_build_copies_are_the_files_of_the_checkout(
    site: Path,
) -> None:
    pairs = {
        "assets/pele.js": "skills/lem/assets/vendor/pele.js",
        "assets/lem.svg": "assets/lem.svg",
        "assets/lem-night.svg": "assets/lem-night.svg",
        "assets/lem-mark.svg": "assets/lem-mark.svg",
        "assets/lem-mark-night.svg": "assets/lem-mark-night.svg",
        **{
            f"assets/screens/{name}-{theme}.png": f"assets/screens/{name}-{theme}.png"
            for name in ("board", "phone", "task")
            for theme in ("light", "dark")
        },
    }
    for built_path, source in pairs.items():
        assert (site / built_path).read_bytes() == (built.ROOT / source).read_bytes(), (
            source
        )

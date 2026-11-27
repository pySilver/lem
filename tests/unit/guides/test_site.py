"""The built site: Zensical builds it from docs/ with no warning, and each page loads nothing
from another host, gives only `lem` lines the command tree takes, links only to what is there,
leads back to the landing page from its logo and its site name, has its Markdown copy and the page
menu, and draws each chart with Pele."""

import json
import re
import shutil
import subprocess
import tomllib
from importlib import resources
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
# The whole site: the landing page at its root, and the docs under docs/.
SITE_ROOT = SITE_URL.removesuffix("docs/")
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
# The site name in Zensical's header, and the link to the landing page that
# overrides/partials/header.html makes of it.
SITE_NAME_SPAN = (
    '<span class="md-ellipsis">\n            {{ config.site_name }}\n          </span>'
)
SITE_NAME_LINK = (
    '<a href="{{ config.extra.homepage | d(nav.homepage.url, true) | url }}" class="md-ellipsis">\n'
    "            {{ config.site_name }}\n"
    "          </a>"
)


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
    pages = {
        built.name_of(site, page) for page in built.pages(site) if not built.leads(page)
    }
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
        if built.leads(page):
            continue
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


def test_every_reference_of_the_whole_site_names_a_file_that_is_there(
    landing: Path,
) -> None:
    # Every page of _site: the landing page, the docs and the pages at the old addresses. A
    # reference that leaves /lem/docs/ is still the site's, so the case above, which reads the
    # docs alone, let four pictures of /lem/assets/ through on 2026-11-27.
    root = urlsplit(SITE_ROOT)
    broken = []
    for page in built.pages(landing):
        base = urljoin(SITE_ROOT, built.name_of(landing, page))
        for tag in built.read(page).tags:
            for name in {tag.attributes.get("href", ""), *fetched(tag)}:
                if not name or name.startswith(("#", "mailto:", "data:")):
                    continue
                parts = urlsplit(urljoin(base, name))
                if (parts.scheme, parts.netloc) != (root.scheme, root.netloc):
                    continue
                path = unquote(parts.path)
                where = f"{built.name_of(landing, page)}: {tag.name} {name}"
                if not path.startswith(root.path):
                    broken.append(f"{where} (outside {SITE_ROOT})")
                    continue
                target = landing / path.removeprefix(root.path)
                if path.endswith("/") or target.is_dir():
                    target /= "index.html"
                if not target.is_file():
                    broken.append(f"{where} (no file {target.relative_to(landing)})")
    assert broken == [], "\n".join(sorted(broken))


def test_the_logo_and_the_site_name_of_each_docs_page_lead_to_the_landing_page(
    landing: Path,
) -> None:
    # The owner, 2026-11-27: "there is no way to return to the landing page from the docs. Logo
    # on top links to `/docs` folder." The header's logo, the menu's logo, the header's site name
    # and the footer's "Lem's home page" lead there; the menu's Overview still leads to the docs'
    # first page.
    landing_page = (built.ROOT / "landing/index.html").read_bytes()
    assert (landing / "index.html").read_bytes() == landing_page
    wrong = []
    for page in built.pages(landing / "docs"):
        if built.leads(page):
            continue
        name = built.name_of(landing, page)
        base = urljoin(SITE_ROOT, name)
        links = [
            (tag.attributes.get("class", ""), urljoin(base, tag.attributes["href"]))
            for tag in built.read(page).tags
            if tag.name == "a" and "href" in tag.attributes
        ]
        home = [
            target
            for kind, target in links
            if "md-logo" in kind.split() or kind in {"md-ellipsis", "lem-home"}
        ]
        overview = [
            target
            for kind, target in links
            if "md-nav__link" in kind.split()
            and target.removesuffix("index.html") == SITE_URL
        ]
        if home != [SITE_ROOT] * 4 or not overview:
            wrong.append(f"{name}: {home}, {len(overview)} link(s) to {SITE_URL}")
    assert wrong == [], "\n".join(wrong)


def test_the_header_is_zensicals_own_with_the_site_name_as_a_link() -> None:
    # overrides/partials/header.html replaces Zensical's header whole, so a Zensical that changes
    # its header would be hidden by the copy: this case fails, and the copy is made again.
    theirs = resources.files("zensical_ui").joinpath("templates/partials/header.html")
    ours = built.ROOT / "overrides/partials/header.html"
    head = re.compile(r"\A\{#-.*?-#\}\n", re.DOTALL)
    expected = head.sub("", theirs.read_text(encoding="utf-8"))
    assert expected.count(SITE_NAME_SPAN) == 1
    expected = expected.replace(SITE_NAME_SPAN, SITE_NAME_LINK)
    assert head.sub("", ours.read_text(encoding="utf-8")) == expected


def test_each_old_address_of_a_guide_leads_to_its_page_under_docs(
    landing: Path,
) -> None:
    # Until 2026-11-27 the guides were at /lem/NAME/; the landing page took /lem/ that day.
    old_root = SITE_URL.removesuffix("docs/")
    for source in NAV:
        if source == "index.md":
            continue
        name = source.removesuffix(".md")
        page = landing / name / "index.html"
        assert page.is_file(), f"no redirect at {old_root}{name}/"
        tags = built.read(page).tags
        meta = [tag.attributes for tag in tags if tag.name == "meta"]
        assert {"http-equiv": "refresh", "content": f"0; url=../docs/{name}/"} in meta
        canonical = [
            tag.attributes["href"]
            for tag in tags
            if tag.name == "link" and tag.attributes.get("rel") == "canonical"
        ]
        assert canonical == [f"{SITE_URL}{name}/"], page
        assert (landing / "docs" / name / "index.html").is_file(), name
        assert not any(tag.name == "script" for tag in tags), page


def test_each_old_address_of_a_moved_guide_leads_to_its_part_of_the_page_that_holds_it(
    landing: Path,
) -> None:
    # On 2026-11-27 the guides of Linear and of GitHub Issues went into one, Start from a ticket.
    moved = {"linear": "linear", "github-issues": "github-issues"}
    ids = built.read(landing / "docs/tickets/index.html").ids
    for name, heading in moved.items():
        assert f"{name}.md" not in NAV, name
        assert heading in ids, heading
        for page, target in (
            (landing / name / "index.html", f"../docs/tickets/#{heading}"),
            (landing / "docs" / name / "index.html", f"../tickets/#{heading}"),
        ):
            tags = built.read(page).tags
            meta = [tag.attributes for tag in tags if tag.name == "meta"]
            assert {"http-equiv": "refresh", "content": f"0; url={target}"} in meta, (
                page
            )
            canonical = [
                tag.attributes["href"]
                for tag in tags
                if tag.name == "link" and tag.attributes.get("rel") == "canonical"
            ]
            assert canonical == [f"{SITE_URL}tickets/#{heading}"], page
            assert not any(tag.name == "script" for tag in tags), page


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
    assert {page for page, _ in charts(site)} == {"index.html", "merge/index.html"}


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


def test_each_turn_of_a_transcript_has_its_speakers_class_and_keeps_its_text(
    site: Path,
) -> None:
    """The owner, 2026-11-27: "Colors per actor would be nice to visually distinct who said
    what". The copy button copies the code's text, so the text stays as it was."""
    node = shutil.which("node")
    if node is None:
        pytest.skip(
            "no node on PATH: brew install node, which the ESLint gate needs too"
        )
    page = site / "index.html"
    assert any(
        tag.name == "script"
        and tag.attributes.get("src", "").endswith("/lem-transcripts.js")
        for tag in built.read(page).tags
    )
    texts = [
        block for kind, block in built.read(page).blocks if "language-text" in kind
    ]
    # a text block that is no transcript: a line of one space, and a turn then a plain line
    others = ["lem doctor\n", "lem  init\nthen a plain line\n"]
    ran = subprocess.run(
        [
            node,
            str(built.ROOT / "tests/unit/guides/speakers.mjs"),
            str(site / "assets/lem-transcripts.js"),
        ],
        input=json.dumps(texts + others),
        capture_output=True,
        text=True,
        check=False,
        timeout=NODE_SECONDS,
    )
    assert ran.returncode == 0, ran.stderr
    found = json.loads(ran.stdout)
    assert found[len(texts) :] == [None, None]
    transcripts = [
        (text, turns) for text, turns in zip(texts, found, strict=False) if turns
    ]
    assert len(transcripts) == 2
    for text, turns in transcripts:
        assert "".join(turn["text"] for turn in turns) == text
        for turn in turns:
            assert turn["className"] == f"lem-turn lem-turn-{turn['speaker']}"
        assert {turn["speaker"] for turn in turns} == {"you", "lem"}


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

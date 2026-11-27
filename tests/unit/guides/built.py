"""The site as `.github/workflows/pages.yml` makes it, in a copy of the checkout, and what the
cases read in it.

The copy holds what the build reads (zensical.toml, docs/, overrides/, landing/ and the files the
links of docs/assets/ name), so a run leaves no _site/ in the checkout. The build runs the lines of
the workflow's step "Build the site" as written, but the `uv sync` that makes .venv: the copy's
.venv is a link to the one this test runs in. Zensical builds with --strict, so a warning (a link
to a page or a heading that is not there) fails it.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ZENSICAL = Path(sys.executable).parent / "zensical"
WORKFLOW = ROOT / ".github/workflows/pages.yml"
STEP = "- name: Build the site"
# What the build reads, by its path in the checkout. The folders of docs/ that zensical.toml
# leaves off the site are copied all the same, so that exclude_docs is what keeps them off.
INPUTS = (
    "zensical.toml",
    "docs",
    "overrides",
    "landing",
    "assets",
    "skills/lem/assets/vendor",
)
# The whole site, and the docs in it, as zensical.toml's site_dir names them.
SITE_DIR = "_site"
DOCS_DIR = "_site/docs"
BUILD_SECONDS = 120


@dataclass(frozen=True)
class Build:
    """A finished build: the folder of the copy, the built docs, the whole site with the landing
    page, and what the build said."""

    folder: Path
    site: Path
    root: Path
    said: str
    code: int


def build_lines() -> list[str]:
    """The lines of the workflow's step "Build the site", but the `uv sync`."""
    text = WORKFLOW.read_text(encoding="utf-8")
    step = text.split(STEP, 1)[1].split("run: |\n", 1)[1]
    lines = []
    for line in step.splitlines():
        if line.strip() and not line.startswith(" " * 10):
            break
        if line.strip() and not line.strip().startswith("uv sync"):
            lines.append(line.strip())
    return lines


def build(into: Path) -> Build:
    """Copy what the build reads into `into`, and build the site there."""
    for name in INPUTS:
        source = ROOT / name
        target = into / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, symlinks=True)
        else:
            shutil.copy2(source, target)
    (into / ".venv").symlink_to(ZENSICAL.parent.parent)
    said, code = "", 0
    for line in build_lines():
        ran = subprocess.run(
            ["/bin/sh", "-c", line],
            cwd=into,
            capture_output=True,
            text=True,
            check=False,
            timeout=BUILD_SECONDS,
            env={"PATH": "/usr/bin:/bin", "NO_COLOR": "1", "HOME": str(into)},
        )
        said += f"$ {line}\n" + re.sub(r"\x1b\[[0-9;]*m", "", ran.stdout + ran.stderr)
        code = ran.returncode
        if code:
            break
    return Build(
        folder=into, site=into / DOCS_DIR, root=into / SITE_DIR, said=said, code=code
    )


def pages(site: Path) -> list[Path]:
    """Every HTML page of the site."""
    return sorted(site.rglob("*.html"))


def leads(page: Path) -> bool:
    """Whether `page` only leads to another page: one at an old address of a guide."""
    return 'http-equiv="refresh"' in page.read_text(encoding="utf-8")


def name_of(site: Path, page: Path) -> str:
    """A page by its path in the site, as a case names it."""
    return str(page.relative_to(site))


@dataclass(frozen=True)
class Tag:
    """One start tag of a page: its name, its attributes, and whether it stands in a <pre>."""

    name: str
    attributes: dict[str, str]
    in_pre: bool


class Reader(HTMLParser):
    """The start tags of a page, the ids it gives, the text of each <pre> block and of each
    <code> outside one."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[Tag] = []
        self.ids: set[str] = set()
        self.blocks: list[tuple[str, str]] = []
        self.spans: list[str] = []
        self.depth_pre = 0
        self.code: list[str] | None = None
        self.block: list[str] | None = None
        self.block_class = ""
        self.language = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        self.tags.append(Tag(tag, attributes, in_pre=self.depth_pre > 0))
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if "name" in attributes and tag == "a":
            self.ids.add(attributes["name"])
        if tag == "div" and "language-" in attributes.get("class", ""):
            self.language = attributes["class"]
        if tag == "pre":
            self.depth_pre += 1
            self.block = []
            self.block_class = f"{attributes.get('class', '')} {self.language}".strip()
            self.language = ""
        elif tag == "code" and self.depth_pre == 0:
            self.code = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self.depth_pre:
            self.depth_pre -= 1
            if self.block is not None:
                self.blocks.append((self.block_class, "".join(self.block)))
            self.block = None
        elif tag == "code" and self.code is not None:
            self.spans.append("".join(self.code))
            self.code = None

    def handle_data(self, data: str) -> None:
        if self.block is not None:
            self.block.append(data)
        if self.code is not None:
            self.code.append(data)


def read(page: Path) -> Reader:
    """A page, read."""
    reader = Reader()
    reader.feed(page.read_text(encoding="utf-8"))
    reader.close()
    return reader

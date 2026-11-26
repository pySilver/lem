"""The site as Zensical builds it, in a copy of the checkout, and what the cases read in it.

The copy holds what the build reads (zensical.toml, docs/, overrides/ and the files the links of
name), so a run leaves no _site/ in the checkout. The build runs as
`.github/workflows/pages.yml` runs it, with --strict: a warning (a link to a page or a heading
that is not there) fails it.
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
# What the build reads, by its path in the checkout.
INPUTS = ("zensical.toml", "docs", "overrides", "assets", "skills/lem/assets/vendor")
# The folders of docs/ that zensical.toml leaves off the site: copied all the same, so that
# exclude_docs is what keeps them off.
SITE_DIR = "_site"
BUILD_SECONDS = 120


@dataclass(frozen=True)
class Build:
    """A finished build: the folder of the copy, the built site, and what Zensical said."""

    folder: Path
    site: Path
    said: str
    code: int


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
    ran = subprocess.run(
        [str(ZENSICAL), "build", "--clean", "--strict"],
        cwd=into,
        capture_output=True,
        text=True,
        check=False,
        timeout=BUILD_SECONDS,
        env={"PATH": "/usr/bin:/bin", "NO_COLOR": "1", "HOME": str(into)},
    )
    said = re.sub(r"\x1b\[[0-9;]*m", "", ran.stdout + ran.stderr)
    return Build(folder=into, site=into / SITE_DIR, said=said, code=ran.returncode)


def pages(site: Path) -> list[Path]:
    """Every HTML page of the site."""
    return sorted(site.rglob("*.html"))


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

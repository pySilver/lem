"""Write a small page at each old address of a guide, which leads to its page under /docs/.

Until 2026-11-27 the guides were at /lem/NAME/; since then they are at /lem/docs/NAME/, and the
landing page is at /lem/. The Pages workflow runs this after the docs are built, as
`.venv/bin/python -I landing/redirects.py _site`. It reads the guides from the nav of
zensical.toml and writes _site/NAME/index.html for each: a meta refresh to ../docs/NAME/ and a
canonical link to the guide's address, with no script. It prints the addresses it wrote as JSON.
"""

import json
import sys
import tomllib
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}: Lem</title>
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={target}">
<meta name="robots" content="noindex">
</head>
<body>
<p>{title} is now at <a href="{target}">{canonical}</a>.</p>
</body>
</html>
"""


def guides(config: dict) -> list[tuple[str, str]]:
    """Each guide of the nav but the docs' first page: its folder name and its title."""
    return [
        (source.removesuffix(".md"), title)
        for entry in config["project"]["nav"]
        for title, source in entry.items()
        if source != "index.md"
    ]


def write(site: Path, config: dict) -> list[str]:
    """Write the page of each old address into `site`, and return the folders written."""
    docs_url = config["project"]["site_url"]
    written = []
    for name, title in guides(config):
        if not (site / "docs" / name / "index.html").is_file():
            raise SystemExit(
                f"{site}/docs/{name}/index.html is not there: build the docs first "
                "(.venv/bin/zensical build --clean --strict)"
            )
        folder = site / name
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(
            PAGE.format(
                title=escape(title),
                canonical=escape(f"{docs_url}{name}/"),
                target=escape(f"../docs/{name}/"),
            ),
            encoding="utf-8",
        )
        written.append(f"{name}/")
    return written


def main() -> None:
    args = sys.argv[1:]
    if len(args) != 1:
        raise SystemExit(
            "usage: redirects.py SITE_DIR (the folder the Pages workflow publishes)"
        )
    config = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
    print(json.dumps({"written": write(Path(args[0]), config)}))


if __name__ == "__main__":
    main()

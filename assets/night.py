#!/usr/bin/env python3
"""Write the night version of the logo: the same drawing, each color replaced by its night color.

    night.py SOURCE TARGET

`assets/lem-night.svg` and `assets/lem-mark-night.svg` are this script's output from `lem.svg` and
`lem-mark.svg`, and `tests/lem-settings.sh` fails when one of them is not. So the drawing is changed
in the day file only, and the night file is written again; a color changes here.

The scene, `lem.svg`, holds both skies. The day sky is one or more groups of the class `c2-sky-day`,
the night sky one group of the class `c2-sky-night`, and the day file hides the night sky with the
rule `HIDE_NIGHT`. The night sky stands in the day file in its night colors, as the owner saw them in
the sample he chose on 2026-11-21: its aurora uses colors of the day field, which `NIGHT` maps for
the mark, so one map cannot serve both. This script maps every color outside the night sky through
`NIGHT`, leaves the colors inside it as written, and swaps the rule so that the night file hides the
day sky. The mark has no sky, so every color of it goes through `NIGHT`.

The picture is the owner's pick ("The Line in the Field"), and so is this palette: he approved it
on 2026-11-14 from a render on a dark page, and the scene with its lights on 2026-11-21. Change
either only on his word.
"""

import re
import sys
from pathlib import Path

NIGHT = {
    # the sky, the field, the plate
    "#b5c5c0": "#0e1a21", "#eadfbe": "#24383d", "#c7a95a": "#4b4226", "#ddbe6c": "#5d5230", "#77725a": "#3c4a4a",
    # the far sheets, the cut stalks, the shadows
    "#f1ead4": "#8f9c98", "#85763c": "#2b2616", "#f3e0a0": "#94864e", "#6a7559": "#161c17",
    # the coat and the cowl
    "#8b9385": "#7c8880", "#6a7a71": "#4f5f5b", "#4e615a": "#33423f", "#a4a895": "#a3ab9f", "#2f4541": "#1b2a2b",
    "#3d514b": "#27383a", "#5d6f66": "#44544f", "#43574f": "#2c3c3a", "#e9dfbc": "#d6cfb0", "#dedbc0": "#c5c8b4",
    "#9da291": "#8c968c", "#6e7d74": "#52625d", "#132427": "#070e10", "#263d40": "#132226",
    # the line, pale at night, with the sleeves and the fingers on it
    "#1d343b": "#d8d0b2", "#a1a593": "#939c90", "#5d6e66": "#44544f", "#1c2f33": "#0c1719",
    "#efe6cb": "#e3dcc0", "#ddd3b5": "#bdb598",
    # the strands, the pegs, the smaller ones
    "#2b4649": "#a9ad99", "#b9773f": "#b0703b", "#5d3a22": "#3a2416",
    "#b06f3e": "#a56638", "#84522f": "#6e4326", "#c07d48": "#b87644", "#2a1d18": "#120c0a",
    # the word, pale like the line
    "#2c4649": "#b9c4b6", "#365350": "#cfd6c4", "#213a3e": "#9fb0a8",
    # the pulse on the line, the pegs' flash and the lit tiles: amber by day, pale gold at night,
    # as the owner's night sample has them
    "#cf6a1c": "#d9a24a", "#f39a2d": "#f2c66e", "#ffe7a0": "#fffbea", "#ffd36a": "#fff1c6", "#e8862a": "#f0b85a",
    # the eye: the same red day and night
    "#ff2a1a": "#ff2a1a",
    # the day sky's sun, rays and the white of its masks: the night file hides that sky, so they stay
    "#fffbea": "#fffbea", "#fff2c8": "#fff2c8", "#f3dc9c": "#f3dc9c", "#fffdf2": "#fffdf2", "#fff6d6": "#fff6d6",
    "#fff0c4": "#fff0c4", "#fff8e2": "#fff8e2", "#ffffff": "#ffffff",
}

DAY_MARK = 'class="c2-sky-day"'
NIGHT_MARK = '<g class="c2-sky-night">'
HIDE_NIGHT = ".c2-sky-night { display: none; }"
HIDE_DAY = ".c2-sky-day { display: none; }"
# a value of a paint, written as an attribute or in the style
PAINT = re.compile(r'\b(fill|stroke|stop-color|flood-color|lighting-color|color)(?:="([^"]*)"|\s*:\s*([^;}"]*))')
FINE = re.compile(r"#[0-9a-f]{6}|none|url\(#[\w-]+\)")


def refuse(text: str) -> None:
    """Exit on every color that is not a six-digit lowercase hex, inside the night sky too."""
    wrong = []
    for found in re.finditer(r"#[0-9A-Fa-f]{3,8}\b", text):
        if not re.fullmatch(r"#[0-9a-f]{6}", found.group(0)):
            wrong.append(found.group(0))
    for found in PAINT.finditer(text):
        value = (found.group(2) if found.group(2) is not None else found.group(3)).strip()
        if not FINE.fullmatch(value) and not re.fullmatch(r"#[0-9A-Fa-f]{3,8}", value):
            wrong.append(f"{found.group(1)} {value}")
    if wrong:
        sys.exit(f"night.py: {', '.join(sorted(set(wrong)))} is no six-digit lowercase hex; write each color as #rrggbb, in lowercase")


def night_group(text: str) -> tuple[int, int]:
    """Where the night sky's group starts and where its closing tag ends."""
    start = text.index(NIGHT_MARK)
    depth = 0
    for tag in re.finditer(r"<g[\s>]|</g>", text[start:]):
        depth += -1 if tag.group(0) == "</g>" else 1
        if depth == 0:
            return start, start + tag.end()
    sys.exit("night.py: the night sky's group is not closed; close its <g> with </g>")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: night.py SOURCE TARGET")
    text = Path(sys.argv[1]).read_text()
    refuse(text)
    days, nights = text.count(DAY_MARK), text.count(NIGHT_MARK)
    if days or nights:
        if not days or nights != 1:
            sys.exit(f"night.py: the scene has {days} group(s) of the day sky and {nights} of the night sky; "
                     f"draw at least one <g {DAY_MARK}> and exactly one {NIGHT_MARK}")
        if text.count(HIDE_NIGHT) != 1 or HIDE_DAY in text:
            sys.exit(f"night.py: the scene's style hides no sky or both; write the rule {HIDE_NIGHT!r} once, and not {HIDE_DAY!r}")
        start, end = night_group(text)
        parts = [text[:start], text[start:end], text[end:]]
        parts[0] = parts[0].replace(HIDE_NIGHT, HIDE_DAY)
    else:
        parts = [text, "", ""]
    outside = parts[0] + parts[2]
    missing = sorted(set(re.findall(r"#[0-9a-f]{6}", outside)) - set(NIGHT))
    if missing:
        sys.exit(f"night.py: no night color for {', '.join(missing)}; add each to NIGHT")
    paint = lambda part: re.sub(r"#[0-9a-f]{6}", lambda found: NIGHT[found.group(0)], part)
    text = paint(parts[0]) + parts[1] + paint(parts[2])
    # The ids get an `n`, so that the day and the night picture can stand inline in one page.
    text = re.sub(r'\b(c2m?)-', r"\1n-", text)
    Path(sys.argv[2]).write_text(text)


if __name__ == "__main__":
    main()

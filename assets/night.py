#!/usr/bin/env python3
"""Write the night version of the logo: the same drawing, each color replaced by its night color.

    night.py SOURCE TARGET

`assets/lem-night.svg` and `assets/lem-mark-night.svg` are this script's output from `lem.svg` and
`lem-mark.svg`, and `tests/test-lem.sh` fails when one of them is not. So the drawing is changed
in the day file only, and the night file is written again; a color changes here.

The picture is the owner's pick ("The Line in the Field"), and so is this palette: he approved it
on 2026-11-14 from a render on a dark page. Change either only on his word.
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
}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: night.py SOURCE TARGET")
    text = Path(sys.argv[1]).read_text()
    missing = sorted(set(re.findall(r"#[0-9a-f]{6}", text)) - set(NIGHT))
    if missing:
        sys.exit(f"night.py: no night color for {', '.join(missing)}; add each to NIGHT")
    text = re.sub(r"#[0-9a-f]{6}", lambda found: NIGHT[found.group(0)], text)
    # The ids get an `n`, so that the day and the night picture can stand inline in one page.
    text = re.sub(r'\b(c2m?)-', r"\1n-", text)
    Path(sys.argv[2]).write_text(text)


if __name__ == "__main__":
    main()

"""The logo, the owner's pick ("The Line in the Field"): the scene and the figure alone, each in its
day and its night file. The scene's light, its signal and its skies are the drawing he approved, held
here byte for byte; a change of it is his word, and its new digest comes with it. night.py writes
each night file from its day file, and refuses a color it cannot map."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets"
NIGHT = ASSETS / "night.py"
# The SHA-256 of each file as main's checks of the scene passed on it (main at bf6d2836, the
# proof of concept: tests/test-site.sh drew and measured these bytes).
APPROVED = {
    "lem.svg": "6765eb88f3fcf15608582959b30c2b74431ebb6c5b6b63a28ff6525dd23b7d60",
    "lem-night.svg": "4c3864e82f5a3faf9146387ab20d57a7f8f9723e39e01b8f148746ad3819429d",
    "lem-mark.svg": "89b4fb191f6427b629fcfd97ca66156685837399658b8034eb8bf7ef53a3ac40",
    "lem-mark-night.svg": "c693743d1bcbb1c61added58510b5a6a807b9d9d51b7eb106fe6e93faea31aab",
}
SCENES = ("lem.svg", "lem-night.svg")
SCENE_BYTES = 50_000
PAINT = re.compile(
    r'\b(fill|stroke|stop-color|flood-color|lighting-color|color)(?:="([^"]*)"|\s*:\s*([^;}"]*))'
)
OUTSIDE = re.compile(
    r"<script\b|<foreignObject\b|<image\b|\son\w+=|@import|(?:href|src)=\"(?!#)[^\"]*\""
    r"|url\((?!#)[^)]*\)"
)
HEX_FIX = "is no six-digit lowercase hex; write each color as #rrggbb"
# The small scene in its night file: the day sky hidden, its color and the field's mapped, the
# night sky's colors as written, and every id with its n.
MAPPED = """<svg><style>.c2n-sky-day { display: none; }</style>
<g class="c2n-sky-day"><rect fill="#0e1a21"/></g>
<g class="c2n-sky-night"><g><rect fill="#b5c5c0"/></g><rect fill="#c7a95a"/></g>
<rect fill="#0e1a21"/></svg>
"""


def night(source: Path, target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-B", str(NIGHT), str(source), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_each_logo_file_is_the_drawing_the_owner_approved() -> None:
    for name, digest in APPROVED.items():
        found = hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()
        assert found == digest, (
            f"assets/{name} changed: the logo changes only on his word"
        )


def test_each_night_logo_is_the_day_logos_drawing_in_the_night_palette(
    tmp_path: Path,
) -> None:
    for name in ("lem", "lem-mark"):
        target = tmp_path / f"{name}-night.svg"
        ran = night(ASSETS / f"{name}.svg", target)
        assert ran.returncode == 0, ran.stderr
        assert target.read_bytes() == (ASSETS / f"{name}-night.svg").read_bytes(), name


def scene(
    tmp_path: Path, day: str, sky: str
) -> tuple[subprocess.CompletedProcess[str], Path]:
    source = tmp_path / "sky.svg"
    source.write_text(
        "\n".join(
            (
                "<svg><style>.c2-sky-night { display: none; }</style>",
                f'<g class="c2-sky-day"><rect fill="{day}"/></g>',
                f'<g class="c2-sky-night"><g><rect fill="{sky}"/></g><rect fill="#c7a95a"/></g>',
                '<rect fill="#b5c5c0"/></svg>',
                "",
            )
        ),
        encoding="utf-8",
    )
    target = tmp_path / "sky-night.svg"
    return night(source, target), target


def test_night_py_keeps_the_night_skys_colors_maps_the_rest_and_refuses_a_wrong_color(
    tmp_path: Path,
) -> None:
    ran, target = scene(tmp_path, "#b5c5c0", "#b5c5c0")
    assert ran.returncode == 0, ran.stderr
    assert target.read_text(encoding="utf-8") == MAPPED
    for day, sky, said in (
        ("#b5c5c0", "#fff", f"#fff {HEX_FIX}"),
        ("#B5C5C0", "#b5c5c0", f"#B5C5C0 {HEX_FIX}"),
        ("#b5c5c0", "red", f"fill red {HEX_FIX}"),
        ("#b5c5c0", "rgb(1, 2, 3)", f"fill rgb(1, 2, 3) {HEX_FIX}"),
    ):
        ran, _ = scene(tmp_path, day, sky)
        assert ran.returncode != 0
        assert said in ran.stderr, ran.stderr
    one = tmp_path / "one-sky.svg"
    one.write_text(
        '<svg><g class="c2-sky-day"><rect fill="#b5c5c0"/></g></svg>\n',
        encoding="utf-8",
    )
    ran = night(one, tmp_path / "out.svg")
    assert (
        "1 group(s) of the day sky and 0 of the night sky; draw at least one"
        in ran.stderr
    )


def test_each_scene_file_is_1600_by_640_small_and_fetches_nothing() -> None:
    for name in SCENES:
        svg = (ASSETS / name).read_text(encoding="utf-8")
        assert len(svg.encode("utf-8")) < SCENE_BYTES, name
        head = re.match(r"<svg\b[^>]*>", svg)
        assert head is not None, name
        for attribute in ('viewBox="0 0 1600 640"', 'width="1600"', 'height="640"'):
            assert attribute in head[0], (name, attribute)
        assert OUTSIDE.findall(svg) == [], name


def test_every_color_of_each_scene_file_is_a_six_digit_lowercase_hex() -> None:
    for name in SCENES:
        svg = (ASSETS / name).read_text(encoding="utf-8")
        wrong = [
            color
            for color in re.findall(r"#[0-9A-Fa-f]{3,8}\b", svg)
            if not re.fullmatch(r"#[0-9a-f]{6}", color)
        ]
        for found in PAINT.finditer(svg):
            value = (found[2] if found[2] is not None else found[3]).strip()
            if not re.fullmatch(r"#[0-9a-f]{6}|none|url\(#[\w-]+\)", value):
                wrong.append(f"{found[1]} {value}")
        assert wrong == [], name


def test_each_scene_file_stops_every_animation_for_reduce_motion() -> None:
    for name in SCENES:
        svg = (ASSETS / name).read_text(encoding="utf-8")
        media = re.findall(
            r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{\s*([^{}]*)\{([^{}]*)\}\s*\}",
            svg,
        )
        assert len(re.findall(r"@media", svg)) == 1, name
        assert media == [("* ", " animation: none !important; ")], name
        assert re.findall(r"<(animate\w*|set)\b", svg) == [], name

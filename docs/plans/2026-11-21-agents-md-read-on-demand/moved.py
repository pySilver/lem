"""moved.py: the check that no word of the rulings and the decisions was lost in the move.

    python3 docs/plans/2026-11-21-agents-md-read-on-demand/moved.py --base 479bef6

It takes each paragraph of "The owner's rulings" and "Decisions the maintaining session took" as
`AGENTS.md` has them at the commit BASE (a list item without its list mark and its indent, or a
block of running text), and looks for it word for word in each file of `docs/rulings/` and
`.lem/decisions/`, with each run of spaces and line breaks taken as one space. It prints the count
compared, the count found and each paragraph it did not find, as JSON, and exits 1 when one is
missing. A paragraph is found when one file holds it whole.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOLDERS = ("docs/rulings", ".lem/decisions")
FIRST = "## The owner's rulings"
AFTER = "## Checks"


def paragraphs(text: str) -> list[tuple[int, str]]:
    """Each paragraph of the two sections, with its first line (1-based)."""
    lines = text.split("\n")
    if FIRST not in lines or AFTER not in lines:
        sys.exit(f"moved.py: AGENTS.md at that commit has no {FIRST!r} or no {AFTER!r}; name the commit before the move as --base")
    out: list[tuple[int, list[str]]] = []
    current = None
    for number in range(lines.index(FIRST) + 1, lines.index(AFTER)):
        line = lines[number]
        if line.startswith("## ") or not line.strip():
            current = None
        elif line.startswith("- "):
            out.append((number + 1, [line[2:]]))
            current = "item"
        elif line.startswith("  ") and current == "item":
            out[-1][1].append(line)
        elif current == "block":
            out[-1][1].append(line)
        else:
            out.append((number + 1, [line]))
            current = "block"
    return [(first, "\n".join(body)) for first, body in out]


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--base":
        sys.exit("moved.py: name the commit before the move, as --base COMMIT (479bef6 for this plan)")
    shown = subprocess.run(["git", "-C", str(ROOT), "show", f"{argv[1]}:AGENTS.md"], capture_output=True, text=True, check=False)
    if shown.returncode != 0:
        sys.exit(f"moved.py: git show {argv[1]}:AGENTS.md failed: {shown.stderr.strip()}; name a commit git knows as --base")
    files = sorted(path for folder in FOLDERS for path in (ROOT / folder).glob("*.md"))
    if not files:
        sys.exit(f"moved.py: no file in {' or '.join(FOLDERS)}; the move has not run in this checkout")
    texts = [flat(path.read_text(encoding="utf-8")) for path in files]
    compared = paragraphs(shown.stdout)
    missing = [{"line": first, "starts": flat(body)[:80]} for first, body in compared if not any(flat(body) in text for text in texts)]
    print(json.dumps({"base": argv[1], "files": len(files), "compared": len(compared), "found": len(compared) - len(missing), "missing": missing}, indent=1))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

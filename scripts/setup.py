#!/usr/bin/env python3
"""Link Lem from this clone into the places an agent reads, and check the machine.

    setup.py            make the links, then run the machine check
    setup.py --check    change nothing: say what is linked, what is absent and what is in the way
    setup.py --remove   remove the links this clone made, and nothing else

It links, for Claude Code:

    skills/NAME/               ->  ~/.claude/skills/NAME        (lem and every lem-NAME)
    agents/lem-builder.md      ->  ~/.claude/agents/lem-builder.md
    skills/lem-huddle/bin/huddle -> ~/.local/bin/huddle

They are links, so an edit in the clone is what the next session reads. A place that already
holds something else is never replaced: the script names it and exits 1, and the owner decides
what goes. A link that points into another clone of Lem is in the way too, because two clones
would then answer to one name.

The last step runs `skills/lem/scripts/doctor.py` and prints its rows that are not found. A
required tool that is absent makes this script exit 1 after the links are made: the links are
right, the machine is not ready.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CLONE = Path(__file__).resolve().parent.parent


def wanted(home: Path, bin_dir: Path) -> list[tuple[Path, Path]]:
    """Each link as (where it goes, what it points at)."""
    links = [(home / ".claude" / "skills" / skill.name, skill) for skill in sorted((CLONE / "skills").iterdir()) if (skill / "SKILL.md").is_file()]
    links.append((home / ".claude" / "agents" / "lem-builder.md", CLONE / "agents" / "lem-builder.md"))
    links.append((bin_dir / "huddle", CLONE / "skills" / "lem-huddle" / "bin" / "huddle"))
    return links


def state(place: Path, target: Path) -> str:
    if place.is_symlink():
        return "linked" if Path(os.path.realpath(place)) == Path(os.path.realpath(target)) else "other link"
    return "taken" if place.exists() else "absent"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="change nothing; report the state of each link")
    parser.add_argument("--remove", action="store_true", help="remove the links this clone made")
    parser.add_argument("--home", type=Path, default=Path.home(), help="the home directory to link into (default: yours)")
    parser.add_argument("--bin", type=Path, help="the directory on PATH for the huddle command (default: HOME/.local/bin)")
    args = parser.parse_args()
    if args.check and args.remove:
        sys.exit("setup.py: --check and --remove do not go together")
    links = wanted(args.home, args.bin or args.home / ".local" / "bin")
    rows = [{"place": str(place), "target": str(target), "state": state(place, target)} for place, target in links]
    in_the_way = [row for row in rows if row["state"] in ("taken", "other link")]

    if args.remove:
        for row in rows:
            if row["state"] == "linked":
                Path(row["place"]).unlink()
                row["state"] = "removed"
        print(json.dumps({"links": rows}, indent=2))
        return
    if in_the_way:
        # Nothing is linked when one place is taken: half a setup answers some commands from this
        # clone and others from whatever was there.
        print(json.dumps({"links": rows}, indent=2))
        named = "; ".join(f"{row['place']} ({'a link to ' + os.path.realpath(row['place']) if row['state'] == 'other link' else 'not a link'})" for row in in_the_way)
        sys.exit(f"setup.py: {len(in_the_way)} place(s) hold something else, and nothing was linked: {named}. Move each away, or leave Lem unlinked")
    if not args.check:
        for row in rows:
            if row["state"] == "absent":
                place = Path(row["place"])
                place.parent.mkdir(parents=True, exist_ok=True)
                place.symlink_to(row["target"])
                row["state"] = "linked"
    on_path = any(Path(entry) == (args.bin or args.home / ".local" / "bin") for entry in os.environ.get("PATH", "").split(os.pathsep) if entry)
    doctor = subprocess.run(
        [sys.executable, "-B", str(CLONE / "skills" / "lem" / "scripts" / "doctor.py")], capture_output=True, text=True, check=False,
        env={**os.environ, "HOME": str(args.home)},
    )
    try:
        machine = json.loads(doctor.stdout)
    except json.JSONDecodeError:
        sys.exit(f"setup.py: doctor.py printed no JSON: {(doctor.stderr or doctor.stdout).strip()}")
    absent = [{"name": row["name"], "need": row["need"], "without_it": row["without_it"]} for row in machine["tools"] if not row["found"]]
    result = {
        "links": rows, "huddle_dir_on_path": on_path, "machine_ok": machine["ok"], "absent": absent,
        "linked": all(row["state"] == "linked" for row in rows),
    }
    print(json.dumps(result, indent=2))
    if not result["linked"]:
        sys.exit("setup.py: not every link is there; run it without --check")
    if not machine["ok"]:
        sys.exit("setup.py: the links are made, and a required tool is absent: " + ", ".join(row["name"] for row in absent if row["need"] == "required"))


if __name__ == "__main__":
    main()

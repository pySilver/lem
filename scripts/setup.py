#!/usr/bin/env python3
"""Link Lem from this clone into the places an agent reads, and check the machine.

    setup.py            make the links, then run the machine check
    setup.py --check    change nothing: say what is linked, what is absent and what is in the way
    setup.py --remove   remove the links this clone made, and nothing else
    setup.py --project DIR [--check | --remove]
                        the same for one repository only: the links go into DIR/.claude

It links, for Claude Code:

    skills/NAME/               ->  ~/.claude/skills/NAME        (lem and every lem-NAME)
    agents/lem-builder.md      ->  ~/.claude/agents/lem-builder.md
    skills/lem-huddle/bin/huddle -> ~/.local/bin/huddle

They are links, so an edit in the clone is what the next session reads. A place that already
holds something else is never replaced: the script names it and exits 1, and the owner decides
what goes. A link that points into another clone of Lem is in the way too, because two clones
would then answer to one name. A link counts as this clone's only when it names the clone's own
path; one that merely ends at the same file by another route is the owner's, and `--remove`
leaves it.

Either every link is made or none: when one cannot be made, the ones this run made are taken
away again, and the report says so. Every run prints the state of all the places as JSON, also a
run that fails.

`--project DIR` is for a trial. Links in the home directory show Lem to every repository on the
machine at once, also to one where another flow still runs with skills of the same use. Links in
one repository's `.claude` folder show Lem there and nowhere else. The `huddle` command is not
linked then, because a command on `PATH` is for the whole machine, and the links are named in a
marked block of that repository's `.git/info/exclude`, so its tree stays clean; `--remove` takes
the block away again. DIR is the main checkout: a worktree shares its exclude file with every
other checkout, so a trial is not linked there. A `.claude` folder that is a link out of the
repository is refused, because the links would then land where the link points, for whoever else
reads that folder.

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


def wanted(home: Path, bin_dir: Path | None) -> list[tuple[Path, Path]]:
    """Each link as (where it goes, what it points at). `home` is a home directory or one repository."""
    links = [(home / ".claude" / "skills" / skill.name, skill) for skill in sorted((CLONE / "skills").iterdir()) if (skill / "SKILL.md").is_file()]
    links.append((home / ".claude" / "agents" / "lem-builder.md", CLONE / "agents" / "lem-builder.md"))
    if bin_dir is not None:
        links.append((bin_dir / "huddle", CLONE / "skills" / "lem-huddle" / "bin" / "huddle"))
    return links


BLOCK = ("# >>> links of a Lem trial (scripts/setup.py --project); --remove takes this block away", "# <<< links of a Lem trial")


def without_block(lines: list[str]) -> list[str]:
    if BLOCK[0] not in lines or BLOCK[1] not in lines:
        return lines
    return lines[:lines.index(BLOCK[0])] + lines[lines.index(BLOCK[1]) + 1:]


def keep_out_of_git(project: Path, places: list[Path] | None) -> None:
    """Name the links in a marked block of the main checkout's exclude file, which git does not
    track; with no places, take the block away."""
    exclude = project / ".git" / "info" / "exclude"
    known = without_block(exclude.read_text().splitlines() if exclude.is_file() else [])
    if places:
        known += [BLOCK[0], *("/" + place.relative_to(project).as_posix() for place in places), BLOCK[1]]
    elif not exclude.is_file():
        return
    exclude.parent.mkdir(exist_ok=True)
    exclude.write_text("\n".join(known) + "\n" if known else "")


def state(place: Path, target: Path) -> str:
    if place.is_symlink():
        # The link's own first step must be the clone's path. Only the folders on the way are
        # resolved, so a home behind a link still counts; the last name is compared as written,
        # so a link that ends at the same file by another route does not.
        hop = Path(os.readlink(place))
        hop = hop if hop.is_absolute() else place.parent / hop
        ours = Path(os.path.realpath(hop.parent)) / hop.name == Path(os.path.realpath(target.parent)) / target.name
        return "linked" if ours else "other link"
    if place.exists():
        return "taken"
    # a file where a folder has to be: nothing can be linked under it
    blocked = next((parent for parent in place.parents if parent.exists() and not parent.is_dir()), None)
    return f"blocked by {blocked}" if blocked else "absent"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="change nothing; report the state of each link")
    parser.add_argument("--remove", action="store_true", help="remove the links this clone made")
    parser.add_argument("--project", type=Path, help="link into this repository's .claude folder only, for a trial")
    parser.add_argument("--home", type=Path, default=Path.home(), help="the home directory to link into (default: yours)")
    parser.add_argument("--bin", type=Path, help="the directory on PATH for the huddle command (default: HOME/.local/bin)")
    args = parser.parse_args()
    if args.check and args.remove:
        sys.exit("setup.py: --check and --remove do not go together")
    project = args.project.resolve() if args.project else None
    if project is not None and not (project / ".git").is_dir():
        sys.exit(
            f"setup.py: --project names the main checkout of a repository, and {project} has no .git folder. "
            "A task's worktree shares its exclude file with every other checkout, so a trial is not linked there",
        )
    bin_dir = None if project else args.bin or args.home / ".local" / "bin"
    links = wanted(project or args.home, bin_dir)
    rows = [{"place": str(place), "target": str(target), "state": state(place, target)} for place, target in links]
    if project is not None:
        # Every place has to be inside the repository for real. A `.claude` that is a link to a
        # shared folder would put the trial's links there, for every reader of that folder, and
        # --remove would then take links away that another setup made.
        for row in rows:
            parent = Path(os.path.realpath(Path(row["place"]).parent))
            if not parent.is_relative_to(project):
                row["state"] = f"blocked by a link that leaves the repository (to {parent})"
    in_the_way = [row for row in rows if row["state"] not in ("linked", "absent")]

    if args.remove:
        stuck = []
        for row in rows:
            if row["state"] == "linked":
                try:
                    Path(row["place"]).unlink()
                    row["state"] = "removed"
                except OSError as error:
                    # go on with the others, so the report is whole: each place says what became of it
                    row["state"] = "linked"
                    row["error"] = str(error)
                    stuck.append(row["place"])
        if project is not None and not any(row["state"] == "linked" for row in rows):
            keep_out_of_git(project, None)
        print(json.dumps({"links": rows}, indent=2))
        if stuck:
            sys.exit(f"setup.py: {len(stuck)} link(s) could not be removed and are still there: {'; '.join(stuck)}")
        return
    if in_the_way:
        # Nothing is linked when one place is taken: half a setup answers some commands from this
        # clone and others from whatever was there.
        print(json.dumps({"links": rows}, indent=2))
        named = "; ".join(
            f"{row['place']} ({'a link to ' + os.readlink(row['place']) if row['state'] == 'other link' else row['state'] if row['state'].startswith('blocked') else 'not a link'})"
            for row in in_the_way
        )
        sys.exit(f"setup.py: {len(in_the_way)} place(s) hold something else, and nothing was linked: {named}. Move each away, or leave Lem unlinked")
    if not args.check:
        if project is not None:
            keep_out_of_git(project, [place for place, _target in links])
        made: list[Path] = []
        try:
            for row in rows:
                if row["state"] == "absent":
                    place = Path(row["place"])
                    place.parent.mkdir(parents=True, exist_ok=True)
                    place.symlink_to(row["target"])
                    made.append(place)
                    row["state"] = "linked"
        except OSError as error:
            # every link or none: take this run's links away again, and say what stopped it
            for place in made:
                place.unlink(missing_ok=True)
            if project is not None and not any(row["state"] == "linked" and Path(row["place"]) not in made for row in rows):
                keep_out_of_git(project, None)
            for row in rows:
                if Path(row["place"]) in made:
                    row["state"] = "absent"
            print(json.dumps({"links": rows}, indent=2))
            sys.exit(f"setup.py: a link could not be made ({error}); the {len(made)} link(s) this run made are removed again, and nothing is linked")
    on_path = bin_dir is not None and any(Path(entry) == bin_dir for entry in os.environ.get("PATH", "").split(os.pathsep) if entry)
    # The check runs where the links are: in the repository for --project, so that it finds the
    # builder agent of that repository.
    doctor = subprocess.run(
        [sys.executable, "-B", str(CLONE / "skills" / "lem" / "scripts" / "doctor.py")], capture_output=True, text=True, check=False,
        env={**os.environ, "HOME": str(args.home)}, cwd=project,
    )
    try:
        machine = json.loads(doctor.stdout)
    except json.JSONDecodeError:
        print(json.dumps({"links": rows}, indent=2))
        sys.exit(f"setup.py: the links are as listed, and the machine check did not run: doctor.py printed no JSON: {(doctor.stderr or doctor.stdout).strip()}")
    absent = [{"name": row["name"], "need": row["need"], "without_it": row["without_it"]} for row in machine["tools"] if not row["found"]]
    result = {
        "links": rows, "scope": str(project) if project else "every repository of this home",
        "huddle": "not linked: a command on PATH is for the whole machine" if project else ("on PATH" if on_path else f"linked in {bin_dir}, which is not on PATH"),
        "machine_ok": machine["ok"], "absent": absent,
        "linked": all(row["state"] == "linked" for row in rows),
    }
    print(json.dumps(result, indent=2))
    if not result["linked"]:
        sys.exit("setup.py: not every link is there; run it without --check")
    if not machine["ok"]:
        sys.exit("setup.py: the links are made, and a required tool is absent: " + ", ".join(row["name"] for row in absent if row["need"] == "required"))


if __name__ == "__main__":
    main()

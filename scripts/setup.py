#!/usr/bin/env python3
"""Link Lem from this clone into the places an agent reads, and check the machine.

    setup.py            make the links, then run the machine check
    setup.py --check    change nothing: say what is linked, what is absent and what is in the way
    setup.py --remove   remove the links this clone made, and nothing else
    setup.py --project DIR [--check | --remove]
                        the same for one repository only: the links go into DIR/.claude
    setup.py --corrections on|off [--project DIR]
                        register the hook that fills a project's queue of corrections, or take it
                        out again; no link is touched

It links, for Claude Code:

    skills/NAME/               ->  ~/.claude/skills/NAME        (lem and every lem-NAME)
    agents/lem-builder.md      ->  ~/.claude/agents/lem-builder.md
    skills/lem-ask/bin/lem-ask -> ~/.local/bin/lem-ask
    skills/lem/scripts/jev.py  ->  ~/.local/bin/jev

They are links, so an edit in the clone is what the next session reads. A place that already
holds something else is never replaced: the script names it and exits 1, and the owner decides
what goes. A link that points into another clone of Lem is in the way too, because two clones
would then answer to one name. A link counts as this clone's only when it names the clone's own
path; one that merely ends at the same file by another route is the owner's, and `--remove`
leaves it.

A skill of the clone that got a new name leaves a link behind with nothing at its end. A link in
one of these folders that points into this clone at a path that is not there any more is such a
leftover: a run that links, and `--remove`, take it away, and `--check` names it. A link of the
owner's own into the clone that still ends somewhere is his, and stays.

Either every link is made or none: when one cannot be made, the ones this run made are taken
away again, and the report says so. Every run prints the state of all the places as JSON, also a
run that fails.

`--project DIR` is for a trial. Links in the home directory show Lem to every repository on the
machine at once, also to one where another flow still runs with skills of the same use. Links in
one repository's `.claude` folder show Lem there and nowhere else. The `lem-ask` and `jev` commands
are not linked then, because a command on `PATH` is for the whole machine. So that the checkout's tree
stays clean, a small `.gitignore` goes beside the links, in `.claude/skills` and `.claude/agents`:
it names the links and itself, and its first line names this clone. It is a file of that one
checkout, so no other worktree is touched; the repository's shared exclude file is not used for
that reason. `--remove` takes away the ignore files this clone wrote, and no other. A folder that
has a `.gitignore` of its own keeps it; when that file does not hide the links, the result says
that git sees them there. A
`.claude` folder that is a link out of the repository is refused, because the links would then
land where the link points, for whoever else reads that folder.

The last step runs `skills/lem/scripts/doctor.py` and prints its rows that are not found. A
required tool that is absent makes this script exit 1 after the links are made: the links are
right, the machine is not ready.

`--corrections on` is the owner's step, on the day of the setup or any later day: the hook sends
each message he types, with the agent message it answers, to the Jev decision model, in every
repository whose settings say `corrections.collect = true`. An agent does not run it for him. It
adds one command to the `UserPromptSubmit` hooks of Claude Code's settings: `~/.claude/settings.json`,
or with `--project DIR` that checkout's own `DIR/.claude/settings.local.json`. The command names
`corrections.py` by the clone's real path, so it needs no link; `python3` and `git` are found on
the hook's `PATH`, as for any hook. The rest of the settings file is kept; the file is written
again as JSON with two spaces. Refused with exit 1, and left as it is: a file that is not JSON,
one whose `UserPromptSubmit` hooks do not have the shape Claude Code reads, one that already
holds this hook in another form (added by hand, another clone's, or this command with another
timeout), and with `--project` a settings file that is a link out of the repository.
`--corrections off` takes out the entry this script writes and no other, and removes a settings
file that then holds nothing. Every other run only reports whether the hook is registered.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"setup.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

CLONE = Path(__file__).resolve().parent.parent
# `python3` and not this run's interpreter: a versioned path of today's Python is gone after its
# next upgrade. Under a Python before 3.11 the hook judges nothing and says so in its log.
HOOK_COMMAND = f"python3 {shlex.quote(str(CLONE / 'skills' / 'lem' / 'scripts' / 'corrections.py'))} hook"
HOOK = {"type": "command", "command": HOOK_COMMAND, "timeout": 10}
ANY_FORM = re.compile(r"corrections\.py['\"]?\s+hook\b")


class Refused(Exception):
    """The settings file is not in a state this script changes; the message names the fix."""


def wanted(home: Path, bin_dir: Path | None) -> list[tuple[Path, Path]]:
    """Each link as (where it goes, what it points at). `home` is a home directory or one repository."""
    links = [(home / ".claude" / "skills" / skill.name, skill) for skill in sorted((CLONE / "skills").iterdir()) if (skill / "SKILL.md").is_file()]
    links.append((home / ".claude" / "agents" / "lem-builder.md", CLONE / "agents" / "lem-builder.md"))
    if bin_dir is not None:
        links.append((bin_dir / "lem-ask", CLONE / "skills" / "lem-ask" / "bin" / "lem-ask"))
        links.append((bin_dir / "jev", CLONE / "skills" / "lem" / "scripts" / "jev.py"))
    return links


def prompt_hooks(file: Path) -> tuple[dict, list[tuple[dict, dict]]]:
    """The settings in `file`, and each command of its UserPromptSubmit hooks as (its group, the hook)."""
    if not file.exists():
        return {}, []
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Refused(f"{file} does not read as JSON ({error}); correct the file, then run this again") from error
    shape = f"{file} does not have the shape of Claude Code's settings"
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise Refused(f"{shape}: the file is an object, and so is its `hooks`; correct the file, then run this again")
    groups = data.get("hooks", {}).get("UserPromptSubmit", [])
    if not isinstance(groups, list) or any(not isinstance(group, dict) or not isinstance(group.get("hooks"), list) for group in groups):
        raise Refused(f"{shape}: `hooks.UserPromptSubmit` is a list of objects, each with a list `hooks`; correct the file, then run this again")
    hooks = [(group, hook) for group in groups for hook in group["hooks"]]
    if any(not isinstance(hook, dict) or (hook.get("type") == "command" and not isinstance(hook.get("command"), str)) for _, hook in hooks):
        raise Refused(f"{shape}: each hook of `hooks.UserPromptSubmit` is an object, and one of the type `command` has a `command`; correct the file, then run this again")
    return data, [(group, hook) for group, hook in hooks if isinstance(hook.get("command"), str)]


def forms(hooks: list[tuple[dict, dict]]) -> tuple[list[tuple[dict, dict]], list[str]]:
    """This script's own entry where it is, and every other form of the hook as its JSON."""
    # The whole entry is compared: the same command with another timeout is not what this script
    # wrote, and a shorter one can end the hook before its two waits do.
    ours = [(group, hook) for group, hook in hooks if hook == HOOK]
    others = [json.dumps(hook, ensure_ascii=False) for _, hook in hooks if hook != HOOK and ANY_FORM.search(hook["command"])]
    return ours, others


def hook_state(file: Path) -> dict:
    """Whether the correction hook is in `file`: registered, not registered, in another form, or unreadable."""
    try:
        _, hooks = prompt_hooks(file)
    except Refused as error:
        return {"file": str(file), "state": "unreadable", "why": str(error)}
    ours, others = forms(hooks)
    row = {"file": str(file), "state": "another form" if others else "registered" if ours else "not registered"}
    if others:
        row["other_forms"] = others
    return row


def write_settings(file: Path, data: dict) -> None:
    # A settings file kept as a link (a folder of dotfiles) stays a link: its target is written.
    real = Path(os.path.realpath(file))
    draft = real.with_name(f"{real.name}.lem-{os.getpid()}")
    try:
        real.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if real.exists():
            shutil.copymode(real, draft)
        os.replace(draft, real)
    except OSError as error:
        # the file is as it was; the draft holds the owner's settings, so it does not stay behind
        draft.unlink(missing_ok=True)
        raise Refused(f"{file} could not be written ({error}) and is as it was; make it writable, then run this again") from error


def corrections(file: Path, turn: str) -> dict:
    """Register this clone's correction hook in `file`, or take it out. Raises Refused and changes nothing."""
    data, hooks = prompt_hooks(file)
    ours, others = forms(hooks)
    if turn == "on":
        if others:
            # two forms of one hook would send and queue each message twice
            raise Refused(f"{file} already holds the correction hook in another form: {'; '.join(others)}. Take that entry out of the file, then run this again")
        if not ours:
            data.setdefault("hooks", {}).setdefault("UserPromptSubmit", []).append({"hooks": [dict(HOOK)]})
            write_settings(file, data)
        return {"file": str(file), "state": "registered", "changed": not ours, "command": HOOK_COMMAND}
    for group, hook in ours:
        group["hooks"] = [other for other in group["hooks"] if other is not hook]
    if ours:
        # a group goes only when this emptied it: one that was empty before is the owner's
        emptied = [group for group, _ in ours if not group["hooks"]]
        groups = [group for group in data["hooks"]["UserPromptSubmit"] if not any(group is gone for gone in emptied)]
        if groups:
            data["hooks"]["UserPromptSubmit"] = groups
        else:
            del data["hooks"]["UserPromptSubmit"]
        if not data["hooks"]:
            del data["hooks"]
        if data:
            write_settings(file, data)
        else:
            # an empty settings file says what no file says
            try:
                Path(os.path.realpath(file)).unlink()
            except OSError as error:
                raise Refused(f"{file} holds nothing but the hook and could not be removed ({error}); remove the file yourself") from error
    row = {"file": str(file), "state": "another form" if others else "not registered", "changed": bool(ours), "file_removed": bool(ours) and not data}
    if others:
        row["other_forms"] = others
    return row


MARK = f"# links of a Lem trial from {CLONE} (scripts/setup.py --project); --remove takes this file away"


def hide_from_git(rows: list[dict]) -> list[str]:
    """Make each folder's ignore file say what is linked there now, and return the folders where
    git still sees the links. Only a file whose first line names this clone is written or removed."""
    visible = []
    folders: dict[Path, list[dict]] = {}
    for row in rows:
        folders.setdefault(Path(row["place"]).parent, []).append(row)
    for folder, members in folders.items():
        if any(row["state"].startswith("blocked") for row in members):
            # not a folder of this repository: whatever is in it belongs to someone else
            continue
        ignore = folder / ".gitignore"
        ours = ignore.is_file() and not ignore.is_symlink() and ignore.read_text().splitlines()[:1] == [MARK]
        linked = [Path(row["place"]).name for row in members if row["state"] == "linked"]
        if (ignore.exists() or ignore.is_symlink()) and not ours:
            # The project's own file stays as it is. It may hide the links already, so git is asked.
            if any(subprocess.run(["git", "-C", str(folder), "check-ignore", "-q", "--", name], capture_output=True, check=False).returncode != 0 for name in linked):
                visible.append(str(folder))
        elif linked:
            ignore.write_text("\n".join([MARK, "/.gitignore", *(f"/{name}" for name in linked)]) + "\n")
        elif ours:
            ignore.unlink()
    return visible


def leftovers(rows: list[dict]) -> list[Path]:
    """Links beside this clone's own that point into the clone at a path that is gone."""
    places = {Path(row["place"]) for row in rows}
    found = []
    for folder in sorted({Path(row["place"]).parent for row in rows if not row["state"].startswith("blocked")}):
        if not folder.is_dir():
            continue
        for entry in sorted(folder.iterdir()):
            if entry in places or not entry.is_symlink():
                continue
            # as in `state`: the link's own first step has to name the clone's path
            hop = Path(os.readlink(entry))
            hop = hop if hop.is_absolute() else entry.parent / hop
            # only a dead one: a link of the owner's own into the clone that still works is his
            if (Path(os.path.realpath(hop.parent)) / hop.name).is_relative_to(CLONE) and not entry.exists():
                found.append(entry)
    return found


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
    parser.add_argument("--corrections", choices=("on", "off"), help="register the hook of the correction queue, or take it out; the owner's step")
    parser.add_argument("--home", type=Path, default=Path.home(), help="the home directory to link into (default: yours)")
    parser.add_argument("--bin", type=Path, help="the directory on PATH for the lem-ask command (default: HOME/.local/bin)")
    args = parser.parse_args()
    if args.check and args.remove:
        sys.exit("setup.py: --check and --remove do not go together")
    if args.corrections and (args.check or args.remove):
        sys.exit("setup.py: --corrections on|off changes the hook and nothing else; run --check or --remove by itself")
    project = args.project.resolve() if args.project else None
    if project is not None and not (project / ".git").exists():
        sys.exit(f"setup.py: {project} is not the root of a git checkout; --project names a repository")
    settings = project / ".claude" / "settings.local.json" if project else args.home / ".claude" / "settings.json"
    if args.corrections:
        # The file itself is resolved, not only its folder: a settings file that is a link to a
        # shared one would register the hook for every checkout that reads the shared file.
        if project is not None and not Path(os.path.realpath(settings)).is_relative_to(project):
            sys.exit(f"setup.py: {settings} is behind a link that leaves the repository (to {os.path.realpath(settings)}); the hook of one repository is not written there")
        try:
            row = corrections(settings, args.corrections)
        except Refused as error:
            sys.exit(f"setup.py: {error}")
        if project is not None and row["state"] == "registered":
            ignored = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", str(settings)], capture_output=True, check=False)
            row["git_sees_the_file"] = ignored.returncode != 0
        print(json.dumps({"corrections_hook": row, "scope": str(project) if project else "every repository of this home"}, indent=2))
        return
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
    old = [{"place": str(place), "target": os.readlink(place), "state": "leftover"} for place in leftovers(rows)]

    def clear_leftovers() -> None:
        for row in old:
            Path(row["place"]).unlink()
            row["state"] = "removed"

    if args.remove:
        stuck = []
        try:
            clear_leftovers()
        except OSError as error:
            stuck.append(f"a leftover ({error})")
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
        if project is not None:
            hide_from_git(rows)
        # the hook is not a link: it stays until `--corrections off`, and the report says so
        print(json.dumps({"links": rows, "leftovers": old, "corrections_hook": hook_state(settings)}, indent=2))
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
    visible: list[str] = []
    if not args.check:
        made: list[Path] = []
        try:
            clear_leftovers()
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
            for row in rows:
                if Path(row["place"]) in made:
                    row["state"] = "absent"
            print(json.dumps({"links": rows}, indent=2))
            sys.exit(f"setup.py: a link could not be made ({error}); the {len(made)} link(s) this run made are removed again, and nothing is linked")
        if project is not None:
            visible = hide_from_git(rows)
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
        "links": rows, "leftovers": old, "scope": str(project) if project else "every repository of this home",
        "commands": "lem-ask and jev are not linked: a command on PATH is for the whole machine" if project else ("on PATH" if on_path else f"linked in {bin_dir}, which is not on PATH"),
        "corrections_hook": hook_state(settings),
        "git_sees_the_links_in": visible, "machine_ok": machine["ok"], "absent": absent,
        "linked": all(row["state"] == "linked" for row in rows) and all(row["state"] == "removed" for row in old),
    }
    print(json.dumps(result, indent=2))
    if not result["linked"]:
        sys.exit("setup.py: not every link is there; run it without --check")
    if not machine["ok"]:
        sys.exit("setup.py: the links are made, and a required tool is absent: " + ", ".join(row["name"] for row in absent if row["need"] == "required"))


if __name__ == "__main__":
    main()

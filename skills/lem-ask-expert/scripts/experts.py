#!/usr/bin/env python3
"""The experts' brief of a choice that waits for the owner, and the record of their answers.

Two experts of two model families answer one choice of a task, of its plan or of its build, from the same brief, at the same
moment, read-only: `fable` and `astra`. This script writes that brief and reads each answer back
into the choice's record; starting the two agents is the harness's (`ask-experts`).

    experts.py brief SLUG N [--file PATH ...]
                     write `experts/choice-N.brief.md` in the task's directory: the choice (what,
                     the options word for word, the recommended one and why, what the personas
                     said), the task's acceptance criteria and its plan, the files the choice is about, and
                     the form of an answer. Refused for a choice that does not wait, and when
                     both experts advised already. Prints the brief's path, each answer's path,
                     the worktree the experts read, and the experts still to ask
    experts.py record SLUG N --expert fable|astra
                     read `experts/choice-N.EXPERT.md`, the expert's last message, and write it
                     into the record with `decisions.py advise`. Refused when the answer is not in
                     the form the brief gives, or picks a text that is no option

An answer is one of two forms, and nothing else:

    pick: THE OPTION, WORD FOR WORD
    why: two to four sentences.

    none fits
    why: two to four sentences.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.exit(f"experts.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

# Lem's own scripts, beside this skill in the same plugin
SCRIPTS = Path(__file__).resolve().parents[2] / "lem" / "scripts"
EXPERTS = ("fable", "astra")


class ExpertError(Exception):
    pass


def script(name: str, repo: Path, *args: str) -> str:
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise ExpertError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    # a line project.py writes on stderr when it succeeds (the move of an older state folder) is this script's to say too
    if ran.returncode == 0 and ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def task_directory(repo: Path, slug: str) -> Path:
    return Path(script("project.py", repo, "state-dir").strip()) / "tasks" / slug


def choice(repo: Path, slug: str, number: int) -> dict:
    found = next((d for d in json.loads(script("decisions.py", repo, "list", slug)) if d["id"] == number), None)
    if found is None or "options" not in found:
        raise ExpertError(f"no choice {number} went to the owner in {slug}: the experts answer a choice that `decisions.py ask` recorded")
    return found


def worktree(repo: Path, slug: str) -> Path:
    """The task's worktree, where criteria.py reads its plan: the experts read the code there."""
    settings = json.loads(script("project.py", repo, "show"))
    root = Path(settings["root"]).resolve()
    return Path(settings["main"]) / Path(settings["paths"]["worktrees"]["path"]).relative_to(root) / slug


def brief_text(slug: str, number: int, found: dict, criteria: dict, place: Path, files: list[Path]) -> str:
    options = "\n".join(f"{n}. {option}" for n, option in enumerate(found["options"], start=1))
    told = "\n".join(f"{criterion['n']}. {criterion['text']}" for criterion in criteria["criteria"]) or "none: the plan has no acceptance criteria"
    kind = f"\n\nSize: {criteria['size']}" + (f", because {criteria['why']}" if criteria.get("why") else "") if criteria.get("size") else ""
    irreversible = (
        f"\nThis step cannot be undone by a later \"no\" ({found['irreversible']}). Your advice goes to the owner; "
        "it never decides this choice, which waits for the owner's word.\n"
    ) if found.get("irreversible") else ""
    listed = "\n".join(f"- {file}" for file in files) or "- none named: read what the choice and the plan point at"
    # a choice asked before the run was a part of the record has none to show
    run = (
        f"\nThe run that ends badly, as the lead {found['case_was']} it:\n\n{found['case']}\n\nWhy it can happen: {found['cause']}\n"
    ) if found.get("case") else ""
    return f"""# Choice {number} of {slug}: the experts' brief

A task met a choice that is the owner's, in its plan or in its build, and the personas left it
unclear, so it waits for the owner. You are one of two experts who answer it from this brief, each on their own. Your answer
goes on the owner's card during the wait. When no answer comes in time, the option both experts
picked is taken; when you split, the recommended option is.

Read only. Change no file, run nothing that writes, and commit nothing. The task's worktree is
`{place}`.

## The choice

{found['what']}
{run}
The options, word for word:

{options}

Recommended: {found['recommended']}. Why: {found['why'].rstrip('.')}.

What the personas said: {found['said']}
{irreversible}
## The acceptance criteria

The task's acceptance criteria, the contract in the owner's words:{kind}

{told}

## The plan

`{criteria['plan']}`. Read it: the criteria are at its top, then the tasks.

## The files the choice is about

{listed}

## Your answer

Your last message is your answer, in one of these two forms and nothing else: no heading, no
quote marks around the option, no text before or after.

    pick: ONE OPTION, COPIED WORD FOR WORD FROM THE LIST ABOVE
    why: two to four sentences: what decides it, from the criteria, the plan or the code.

    none fits
    why: two to four sentences: why no option fits, and what would.
"""


def cmd_brief(repo: Path, slug: str, number: int, names: list[str]) -> dict:
    found = choice(repo, slug, number)
    if found["state"] != "waits":
        raise ExpertError(f"choice {number} of {slug} does not wait: it is {found['state']}, with {found.get('chose')!r}; the experts answer a choice that waits")
    advised = found.get("advice", {})
    ask = [name for name in EXPERTS if name not in advised]
    if not ask:
        raise ExpertError(f"choice {number} of {slug} has the advice of both experts already: `decisions.py list {slug}` shows it")
    place = worktree(repo, slug)
    try:
        criteria = json.loads(script("criteria.py", repo, "show", slug))
    except ExpertError as error:
        raise ExpertError(f"the brief needs the task's criteria and plan, and criteria.py says: {error}") from error
    files = []
    for name in names:
        path = Path(name) if Path(name).is_absolute() else place / name
        if not path.exists():
            raise ExpertError(f"--file {name} is not in the task's worktree ({place}): name a file the choice is about, relative to the worktree")
        files.append(path.resolve())
    directory = task_directory(repo, slug) / "experts"
    directory.mkdir(parents=True, exist_ok=True)
    brief = directory / f"choice-{number}.brief.md"
    brief.write_text(brief_text(slug, number, found, criteria, place, files), encoding="utf-8")
    return {
        "task": slug, "choice": number, "brief": str(brief), "worktree": str(place),
        "answers": {name: str(directory / f"choice-{number}.{name}.md") for name in EXPERTS},
        "ask": ask, "advised": sorted(advised),
        "next": f"start {' and '.join(ask)} at once, in the background, with this brief (the harness's `ask-experts`); "
                f"as each ends, `experts.py record {slug} {number} --expert NAME`",
    }


# The two forms of an answer, with any indent an expert copied from the brief
ANSWER = re.compile(r"\A(?:pick:[ \t]*(?P<pick>\S[^\n]*?)|(?P<none>none fits))[ \t]*\n\s*why:[ \t]*(?P<why>\S.*)\Z", re.DOTALL | re.IGNORECASE)


def cmd_record(repo: Path, slug: str, number: int, expert: str) -> dict:
    answer = task_directory(repo, slug) / "experts" / f"choice-{number}.{expert}.md"
    if not answer.is_file():
        raise ExpertError(f"{answer} is not there: {expert}'s last message goes into it word for word before it is recorded")
    try:
        written = answer.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ExpertError(f"{answer} is not UTF-8 text (byte {error.start} does not read): write {expert}'s last message into it as it came") from error
    found = ANSWER.match(written.strip())
    if found is None:
        raise ExpertError(
            f"{answer} is not an answer in the brief's form (`pick: OPTION` or `none fits`, then `why: ...`). "
            f"Ask {expert} once more with the same brief. When that answer is refused too, record nothing for {expert} and say so "
            "in one line: with one expert's advice the end of the wait takes the recommended option",
        )
    why = " ".join(found["why"].split())
    if found["none"]:
        return json.loads(script("decisions.py", repo, "advise", slug, str(number), "--expert", expert, "--none", "--why", why))
    return json.loads(script("decisions.py", repo, "advise", slug, str(number), "--expert", expert, "--pick", found["pick"].strip(), "--why", why))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    brief = commands.add_parser("brief")
    brief.add_argument("slug")
    brief.add_argument("id", type=int)
    brief.add_argument("--file", action="append", default=[], metavar="PATH", help="a file the choice is about, relative to the task's worktree")
    record = commands.add_parser("record")
    record.add_argument("slug")
    record.add_argument("id", type=int)
    record.add_argument("--expert", required=True, choices=EXPERTS)
    args = parser.parse_args()
    for arg in sys.argv[1:]:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            sys.exit(f"experts.py: the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8")
    repo = Path(args.repo)
    try:
        if args.command == "brief":
            result = cmd_brief(repo, args.slug, args.id, args.file)
        else:
            result = cmd_record(repo, args.slug, args.id, args.expert)
    except ExpertError as error:
        sys.exit(f"experts.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The experts' brief of one question, and the record of their answers.

Two experts of two model families answer one question from the same brief, at the same moment,
read-only. Who they are is the settings' `seats.experts`, two seats `agent/model:effort` that
`lem project show` prints; `--seat`, once for each expert, names them for one call instead. A
choice of a task keeps their advice in two places, `fable` for the first seat and `astra` for the
second, whatever model sits there, and that place is the expert's name. For a question in words
an expert's name is the last word of its model that holds a letter (`opus`, `sol`), or its place
when its seat names no model. Its answer file carries the name. This script writes the brief and
reads each answer back; starting the agents is the harness's (`ask-experts`).

A question in words, which the owner asks (`/lem ask-expert ...`), has a folder of its own in Lem's
state folder, `experts/DATE-TIME-WORDS/`, with the brief, each expert's answer and `record.json`:

    lem experts brief --question TEXT [--context TEXT] [--option TEXT ...] [--file PATH ...]
                     make the folder and write `brief.md` in it: the question, what is being
                     decided (`--context`), the options word for word when there are any, the
                     files that matter, and the form of an answer. Prints the folder's name, the
                     brief's path, each expert with its seat and its answer file, and the checkout
                     the experts read. Folders older than KEEP_DAYS are removed first
    lem experts record --folder NAME --expert NAME
                     read the expert's answer file, its last message, and write it into the
                     folder's `record.json`. Refused when the answer is not in the brief's form,
                     picks a text that is no option, or the expert answered already. Prints the
                     record: each answer, whether all who answered share a pick (`agree`), and who
                     is still to answer (`waiting`)

A choice of a task that waits for the owner, which Lem's stages give the experts right after
`lem decisions ask`, keeps its brief in the task's directory and its advice in the choice's record:

    lem experts brief SLUG N [--file PATH ...]
                     write `experts/choice-N.brief.md` in the task's directory: the choice (what,
                     the options word for word, the recommended one and why, what the personas
                     said), the task's acceptance criteria and its plan, the files the choice is
                     about, and the form of an answer. Refused for a choice that does not wait, and
                     when every expert advised already
    lem experts record SLUG N --expert NAME
                     read `experts/choice-N.NAME.md` and write it into the record with
                     `lem decisions advise`, under the same refusals as above

An answer is one of these forms, and nothing else; the last one only for a question with no
options:

    pick: THE OPTION, WORD FOR WORD
    why: two to four sentences.

    none fits
    why: two to four sentences.

    answer: one to three sentences.
    why: two to four sentences.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.exit(f"experts.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# Lem's own scripts, beside this skill in the same plugin
SCRIPTS = Path(__file__).resolve().parents[2] / "lem" / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
# the places in which a task's record keeps the experts' advice: decisions.py's, and nobody else's;
# the first seat answers in the first, the second in the second (project.py's EXPERT_PLACES)
from decisions import EXPERTS as PLACES  # noqa: E402

# A seat for the error messages, in the form `--seat` takes.
EXAMPLE_SEAT = "codex/gpt-6-astra:high"
# The agents whose way to start an expert the harness gives.
AGENTS = ("claude", "codex")
# A seat as `--seat` takes it: the model and the effort may be left out, and are then that agent's
# own default.
SEAT = re.compile(r"\A(?P<agent>[a-z]+)(?:/(?P<model>[A-Za-z0-9][A-Za-z0-9._-]*))?(?::(?P<effort>[a-z]+))?\Z")
# How long the folder of a question in words is kept after its last write. A guess, not a
# measurement: long enough for the owner to look back at an answer in the same piece of work.
KEEP_DAYS = 30
FOLDER = re.compile(r"\A\d{4}-\d{2}-\d{2}-\d{6}-[a-z0-9-]+\Z")


class ExpertError(Exception):
    pass


def script(name: str, repo: Path, *args: str) -> str:
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise ExpertError(ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed")
    # a line project.py writes on stderr when it succeeds (the move of an older state folder) is this script's to say too
    if ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def state_folder(repo: Path) -> Path:
    return Path(script("project.py", repo, "state-dir").strip())


def task_directory(repo: Path, slug: str) -> Path:
    return state_folder(repo) / "tasks" / slug


def name_of(model: str) -> str:
    """An expert's name: the last word of its model that holds a letter (`gpt-6-astra` is astra)."""
    words = [word for word in re.split(r"[-_.]", model.lower()) if re.search(r"[a-z]", word)]
    return words[-1] if words else model.lower()


def parse_seat(given: str, where: str, place: str | None) -> dict:
    """One `--seat`, as `lem project show` gives a seat of the settings: its parts, each None when
    the seat leaves it out, and its place in a choice's record."""
    found = SEAT.match(given)
    if found is None:
        raise ExpertError(f"{where} {given!r} is no seat: write it as agent/model:effort, for example {EXAMPLE_SEAT}")
    if found["agent"] not in AGENTS:
        raise ExpertError(f"{where} {given!r} names the agent {found['agent']!r}: an expert is started by {' or '.join(AGENTS)}, the agents the harness knows")
    return {"seat": found.group(0), **found.groupdict(), "place": place}


def seats(repo: Path, given: list[str], by_place: bool = False) -> list[dict]:
    """The experts, each with its seat's parts and its place: `--seat` when given, in the order
    given, else the settings' `seats.experts` as `lem project show` resolves them (the project's,
    this machine's own, or Lem's default). Each is named by its place for a choice of a task
    (`by_place`), and by its model for a question in words."""
    if given:
        experts = [parse_seat(seat, "--seat", PLACES[number] if number < len(PLACES) else None) for number, seat in enumerate(given)]
    else:
        named = json.loads(script("project.py", repo, "show"))["seats"]["experts"]
        experts = [{key: seat.get(key) for key in ("seat", "agent", "model", "effort", "place")} for seat in named]
    for expert in experts:
        expert["name"] = expert["place"] if by_place else name_of(expert["model"]) if expert["model"] else expert["place"] or expert["agent"]
    names = [expert["name"] for expert in experts]
    twice = sorted({name for name in names if names.count(name) > 1})
    if twice:
        raise ExpertError(f"two experts are named {', '.join(twice)} ({', '.join(e['seat'] for e in experts)}): each answer file carries the name, so give models whose last words differ")
    return experts


def checkout(repo: Path) -> Path:
    ran = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        raise ExpertError(f"{repo} is not inside a git checkout: the experts read a checkout, so give --repo one")
    return Path(ran.stdout.strip()).resolve()


def named_files(place: Path, names: list[str], where: str) -> list[Path]:
    files = []
    for name in names:
        path = Path(name) if Path(name).is_absolute() else place / name
        if not path.exists():
            raise ExpertError(f"--file {name} is not in {where} ({place}): name a file that matters, relative to it")
        files.append(path.resolve())
    return files


def answer_form(options: list[str], pick_from: str) -> str:
    if options:
        return f"""    pick: ONE OPTION, COPIED WORD FOR WORD FROM {pick_from}
    why: two to four sentences: what decides it, from the criteria, the plan or the code.

    none fits
    why: two to four sentences: why no option fits, and what would."""
    return """    answer: one to three sentences: your answer to the question.
    why: two to four sentences: what decides it, from the code, the files or what you know."""


# --- a choice of a task ---------------------------------------------------------------------

def choice(repo: Path, slug: str, number: int) -> dict:
    found = next((d for d in json.loads(script("decisions.py", repo, "list", slug)) if d["id"] == number), None)
    if found is None or "options" not in found:
        raise ExpertError(f"no choice {number} went to the owner in {slug}: the experts answer a choice that `lem decisions ask` recorded")
    return found


def worktree(repo: Path, slug: str) -> Path:
    """The task's worktree, where criteria.py reads its plan: the experts read the code there."""
    settings = json.loads(script("project.py", repo, "show"))
    root = Path(settings["root"]).resolve()
    return Path(settings["main"]) / Path(settings["paths"]["worktrees"]["path"]).relative_to(root) / slug


def choice_experts(repo: Path, given: list[str]) -> list[dict]:
    """The two experts of a choice of a task, each named by its place in the record, whatever
    model sits there."""
    experts = seats(repo, given, by_place=True) if len(given) in (0, len(PLACES)) else None
    if experts is None or [expert["place"] for expert in experts] != list(PLACES):
        raise ExpertError(
            f"a choice of a task has {len(PLACES)} experts, and its record keeps their advice as {' and '.join(PLACES)}: "
            f"give --seat {len(PLACES)} times, the first for {PLACES[0]} and the second for {PLACES[1]}, or leave it out for the settings' seats.experts",
        )
    return experts


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

{answer_form(found['options'], 'THE LIST ABOVE')}
"""


def cmd_choice_brief(repo: Path, slug: str, number: int, names: list[str], given: list[str]) -> dict:
    experts = choice_experts(repo, given)
    found = choice(repo, slug, number)
    if found["state"] != "waits":
        raise ExpertError(f"choice {number} of {slug} does not wait: it is {found['state']}, with {found.get('chose')!r}; the experts answer a choice that waits")
    advised = found.get("advice", {})
    ask = [expert["name"] for expert in experts if expert["name"] not in advised]
    if not ask:
        raise ExpertError(f"choice {number} of {slug} has the advice of both experts already: `lem decisions list {slug}` shows it")
    place = worktree(repo, slug)
    try:
        criteria = json.loads(script("criteria.py", repo, "show", slug))
    except ExpertError as error:
        raise ExpertError(f"the brief needs the task's criteria and plan, and criteria.py says: {error}") from error
    files = named_files(place, names, "the task's worktree")
    directory = task_directory(repo, slug) / "experts"
    directory.mkdir(parents=True, exist_ok=True)
    brief = directory / f"choice-{number}.brief.md"
    brief.write_text(brief_text(slug, number, found, criteria, place, files), encoding="utf-8")
    answers = {expert["name"]: str(directory / f"choice-{number}.{expert['name']}.md") for expert in experts}
    return {
        "task": slug, "choice": number, "brief": str(brief), "worktree": str(place),
        "experts": [{**expert, "answer": answers[expert["name"]]} for expert in experts],
        "answers": answers, "ask": ask, "advised": sorted(advised),
        "next": f"start {' and '.join(ask)} at once, in the background, with this brief (the harness's `ask-experts`); "
                f"as each ends, `lem experts record {slug} {number} --expert NAME`",
    }


# The forms of an answer, with any indent an expert copied from the brief
ANSWER = re.compile(r"\A(?:pick:[ \t]*(?P<pick>\S[^\n]*?)|(?P<none>none fits))[ \t]*\n\s*why:[ \t]*(?P<why>\S.*)\Z", re.DOTALL | re.IGNORECASE)
FREE = re.compile(r"\Aanswer:[ \t]*(?P<answer>\S.*?)\n\s*why:[ \t]*(?P<why>\S.*)\Z", re.DOTALL | re.IGNORECASE)


def read_answer(answer: Path, expert: str, options: bool, one_left: str) -> dict:
    if not answer.is_file():
        raise ExpertError(f"{answer} is not there: {expert}'s last message goes into it word for word before it is recorded")
    try:
        written = answer.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ExpertError(f"{answer} is not UTF-8 text (byte {error.start} does not read): write {expert}'s last message into it as it came") from error
    found = (ANSWER if options else FREE).match(written.strip())
    if found is None:
        form = "`pick: OPTION` or `none fits`, then `why: ...`" if options else "`answer: ...`, then `why: ...`"
        raise ExpertError(
            f"{answer} is not an answer in the brief's form ({form}). "
            f"Ask {expert} once more with the same brief. When that answer is refused too, record nothing for {expert} and say so "
            f"in one line: {one_left}",
        )
    why = " ".join(found["why"].split())
    if not options:
        return {"answer": " ".join(found["answer"].split()), "why": why}
    if found["none"]:
        return {"none": True, "why": why}
    return {"pick": found["pick"].strip(), "why": why}


def cmd_choice_record(repo: Path, slug: str, number: int, expert: str, given: list[str]) -> dict:
    names = [e["name"] for e in choice_experts(repo, given)]
    if expert not in names:
        raise ExpertError(f"--expert {expert} is none of the experts ({', '.join(names)})")
    got = read_answer(task_directory(repo, slug) / "experts" / f"choice-{number}.{expert}.md", expert, options=True,
                      one_left="with one expert's advice the end of the wait takes the recommended option")
    if got.get("none"):
        return json.loads(script("decisions.py", repo, "advise", slug, str(number), "--expert", expert, "--none", "--why", got["why"]))
    return json.loads(script("decisions.py", repo, "advise", slug, str(number), "--expert", expert, "--pick", got["pick"], "--why", got["why"]))


# --- a question in words --------------------------------------------------------------------

def questions(repo: Path) -> Path:
    return state_folder(repo) / "experts"


def prune(top: Path, now: float) -> list[str]:
    """Remove the folders of questions whose last write is older than KEEP_DAYS; their names."""
    removed = []
    for folder in sorted(top.iterdir()) if top.is_dir() else []:
        if not folder.is_dir() or not FOLDER.match(folder.name):
            continue
        last = max([folder.stat().st_mtime] + [path.stat().st_mtime for path in folder.iterdir()])
        if now - last > KEEP_DAYS * 86400:
            shutil.rmtree(folder, ignore_errors=True)
            removed.append(folder.name)
    return removed


def new_folder(top: Path, question: str, at: datetime) -> Path:
    words = "-".join(re.findall(r"[a-z0-9]+", question.lower())[:6])[:48].strip("-") or "question"
    stem = f"{at.strftime('%Y-%m-%d-%H%M%S')}-{words}"
    top.mkdir(parents=True, exist_ok=True)
    for n in range(1, 100):
        folder = top / (stem if n == 1 else f"{stem}-{n}")
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            continue
    raise ExpertError(f"99 folders named {stem} are in {top}: remove some, then ask again")


def free_brief_text(question: str, context: str, options: list[str], place: Path, files: list[Path], count: int) -> str:
    decided = f"\n## What is being decided\n\n{context.strip()}\n" if context.strip() else ""
    listed = "\n".join(f"- {file}" for file in files) or "- none named: read what the question points at"
    if options:
        offered = "\n## The options, word for word\n\n" + "\n".join(f"{n}. {option}" for n, option in enumerate(options, start=1)) + "\n"
        forms = "one of these two forms"
    else:
        offered = "\nNo options were given: answer the question itself.\n"
        forms = "this form"
    return f"""# A question for the experts

The owner asks {count} experts of different model families one question, and each answers it from
this brief on their own. Your answer goes to the owner beside the others'. It decides nothing by
itself.

Read only. Change no file, run nothing that writes, and commit nothing. The checkout is
`{place}`.

## The question

{question.strip()}
{decided}{offered}
## The files that matter

{listed}

## Your answer

Your last message is your answer, in {forms} and nothing else: no heading, no quote marks, no
text before or after.

{answer_form(options, 'THE OPTIONS ABOVE')}
"""


def write_record(folder: Path, record: dict) -> None:
    staging = folder / f".record.{os.getpid()}"
    staging.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(staging, folder / "record.json")


def summary(folder: Path, record: dict) -> dict:
    answers = record["answers"]
    picks = {answer.get("pick") for answer in answers.values()}
    shared = picks.pop() if record["options"] and len(answers) > 1 and len(picks) == 1 else None
    waiting = [expert["name"] for expert in record["experts"] if expert["name"] not in answers]
    if waiting:
        then = f"wait for {' and '.join(waiting)}; as each ends, `lem experts record --folder {folder.name} --expert NAME`"
    elif record["options"]:
        then = "show the owner the answers side by side, " + (f"all picked {shared!r}" if shared else "where they split") + ", and one line of what you would do with them"
    else:
        then = "show the owner the answers side by side, where they agree and where they split, and one line of what you would do with them"
    return {"folder": folder.name, "dir": str(folder), **record, "agree": shared, "waiting": waiting, "next": then}


def cmd_free_brief(repo: Path, question: str, context: str, options: list[str], names: list[str], given: list[str]) -> dict:
    if not question.strip():
        raise ExpertError("--question is empty: give the question in words")
    if len(set(options)) != len(options):
        raise ExpertError("two --option are the same text: give each option once")
    if len(options) == 1:
        raise ExpertError("one --option is no choice: give two or more, or none for an open question")
    experts = seats(repo, given)
    place = checkout(repo)
    files = named_files(place, names, "the checkout")
    top = questions(repo)
    now = datetime.now(timezone.utc)
    removed = prune(top, now.timestamp())
    folder = new_folder(top, question, now)
    (folder / "brief.md").write_text(free_brief_text(question, context, options, place, files, len(experts)), encoding="utf-8")
    record = {
        "question": question.strip(), "context": context.strip(), "options": options, "files": [str(file) for file in files],
        "asked": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "checkout": str(place),
        "experts": [{**expert, "answer": str(folder / f"{expert['name']}.md")} for expert in experts], "answers": {},
    }
    write_record(folder, record)
    names_ = [expert["name"] for expert in experts]
    return {
        "folder": folder.name, "dir": str(folder), "brief": str(folder / "brief.md"), "worktree": str(place),
        "experts": record["experts"], "answers": {expert["name"]: expert["answer"] for expert in record["experts"]},
        "ask": names_, "removed": removed,
        "next": f"start {' and '.join(names_)} at once, in the background, with this brief (the harness's `ask-experts`); "
                f"as each ends, `lem experts record --folder {folder.name} --expert NAME`",
    }


def cmd_free_record(repo: Path, name: str, expert: str) -> dict:
    if not FOLDER.match(name):
        raise ExpertError(f"--folder {name!r} is no question's folder: give the name `lem experts brief --question` printed")
    folder = questions(repo) / name
    if not (folder / "record.json").is_file():
        raise ExpertError(f"no question {name} is in {folder.parent}: give the name `lem experts brief --question` printed; a folder older than {KEEP_DAYS} days is removed")
    with open(folder / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        names = [e["name"] for e in record["experts"]]
        if expert not in names:
            raise ExpertError(f"--expert {expert} is none of this question's experts ({', '.join(names)})")
        if expert in record["answers"]:
            raise ExpertError(f"{expert} answered question {name} already: its answer is in {folder / 'record.json'}")
        got = read_answer(folder / f"{expert}.md", expert, options=bool(record["options"]), one_left="the owner then has the other experts' answers only")
        if "pick" in got and got["pick"] not in record["options"]:
            raise ExpertError(f"the pick of an expert is one of the options, word for word: {'; '.join(record['options'])}; {got['pick']!r} is none of them")
        record["answers"][expert] = {**got, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        write_record(folder, record)
    return summary(folder, record)


def main() -> None:
    parser = argparse.ArgumentParser(prog="lem experts", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    brief = commands.add_parser("brief")
    brief.add_argument("slug", nargs="?")
    brief.add_argument("id", nargs="?", type=int)
    brief.add_argument("--question", help="a question in words, which has a folder of its own")
    brief.add_argument("--context", default="", help="what is being decided, and why it came up")
    brief.add_argument("--option", action="append", default=[], help="an option, word for word, once for each")
    brief.add_argument("--file", action="append", default=[], metavar="PATH", help="a file that matters, relative to the checkout or the task's worktree")
    record = commands.add_parser("record")
    record.add_argument("slug", nargs="?")
    record.add_argument("id", nargs="?", type=int)
    record.add_argument("--folder", help="the folder of a question in words, as brief printed it")
    record.add_argument("--expert", required=True)
    for each in (brief, record):
        each.add_argument("--seat", action="append", default=[], metavar="AGENT/MODEL:EFFORT", help="an expert, once for each, in the place of the settings' seats.experts")
    args = parser.parse_args()
    for arg in sys.argv[1:]:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            sys.exit(f"experts.py: the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8")
    repo = Path(args.repo)
    choice_form = args.slug is not None and args.id is not None
    words = args.question if args.command == "brief" else args.folder
    if choice_form == (words is not None) or (args.slug is not None and args.id is None):
        flag = "--question TEXT" if args.command == "brief" else "--folder NAME"
        sys.exit(f"experts.py: {args.command} takes a task's SLUG N or {flag}, one of the two")
    try:
        if args.command == "brief" and choice_form:
            if args.context or args.option:
                raise ExpertError("--context and --option belong to a question in words: a task's choice has its own, in its record")
            result = cmd_choice_brief(repo, args.slug, args.id, args.file, args.seat)
        elif args.command == "brief":
            result = cmd_free_brief(repo, args.question, args.context, args.option, args.file, args.seat)
        elif choice_form:
            result = cmd_choice_record(repo, args.slug, args.id, args.expert, args.seat)
        else:
            if args.seat:
                raise ExpertError("--seat belongs to brief: a question's experts are the ones its brief named")
            result = cmd_free_record(repo, args.folder, args.expert)
    except ExpertError as error:
        sys.exit(f"experts.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

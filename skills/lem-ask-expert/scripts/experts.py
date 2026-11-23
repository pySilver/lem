#!/usr/bin/env python3
"""The experts' brief of one question, and the record of their answers.

Two experts of two model families answer one question from the same brief, at the same moment,
read-only, or one expert alone on a machine with one of their agents. Who they are is the
settings' `seats.experts`, one or two seats `agent/model:effort` that `lem project show` prints,
each that is `here` (its agent is on this machine); `--seat`, once for each expert, names them for
one call instead. An expert's name is the last word of its model that holds a letter (`opus`,
`sol`), or its place (`fable` for the first seat, `astra` for the second) when a `--seat` names no
model: a seat of the settings is written whole. Its answer file carries the name. This script writes the brief and
reads each answer back; starting the agents is the harness's (`ask-experts`).

A question in words, which the owner asks (`/lem ask-expert ...`) and which a lead's ladder asks at
its last level (`stages/ladder.md`, the experts), has a folder of its own in Lem's state folder, `experts/DATE-TIME-WORDS/`, with the brief, each expert's answer and `record.json`. The folder goes
`state.keep_days` days after its last write (`lem project prune`):

    lem experts brief --question TEXT [--context TEXT] [--option TEXT ...] [--file PATH ...]
                     make the folder and write `brief.md` in it: the question, what is being
                     decided (`--context`), the options word for word when there are any, the
                     files that matter, who the code is for, and the form of an answer. Prints the folder's name, the
                     brief's path, each expert with its seat and its answer file, and the checkout
                     the experts read
    lem experts record --folder NAME --expert NAME
                     read the expert's answer file, its last message, and write it into the
                     folder's `record.json`. Refused when the answer is not in the brief's form,
                     picks a text that is no option, or the expert answered already. Prints the
                     record: each answer, whether all who answered share a pick (`agree`), and who
                     is still to answer (`waiting`)

Who the code is for is a part of each brief: the project's profile by its path, and each of
its personas by its file's path, its first heading and its "Who they are" (WHO_WORDS words at most),
from what `lem cast` prints, with the sentence that an expert weighs an option by what it does to
these people and still decides as an engineer. A project with no personas has a setup that is not
finished, and its brief is refused with what `lem cast` says.

An answer is one of these forms, and nothing else; the last one only for a question with no
options:

    pick: THE OPTION, WORD FOR WORD
    why: two to four sentences.

    none fits
    why: two to four sentences.

    answer: one to three sentences.
    why: two to four sentences.
"""

import sys

if sys.version_info < (3, 11):
    sys.exit(
        f"experts.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it"
    )

import argparse
import fcntl
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# Lem's own scripts, beside this skill in the same plugin
SCRIPTS = Path(__file__).resolve().parents[2] / "lem" / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
# the names of the two seats of the settings' seats.experts, the first and the second, whatever model
# sits there (project.py's EXPERT_PLACES): an expert whose `--seat` names no model is named by its place
PLACES = ("fable", "astra")

# A seat for the error messages, in the form `--seat` takes.
EXAMPLE_SEAT = "codex/gpt-6.2-astra:high"
# The agents whose way to start an expert the harness gives.
AGENTS = ("claude", "codex")
# A seat as `--seat` takes it: the model and the effort may be left out, and are then that agent's
# own default.
SEAT = re.compile(
    r"\A(?P<agent>[a-z]+)(?:/(?P<model>[A-Za-z0-9][A-Za-z0-9._-]*))?(?::(?P<effort>[a-z]+))?\Z"
)
FOLDER = re.compile(r"\A\d{4}-\d{2}-\d{2}-\d{6}-[a-z0-9-]+\Z")
# The persona panel's script, beside this skill in the same plugin: the one reader of the cast and
# the profile, which a brief names so that an expert knows who the code is for.
CAST = Path(__file__).resolve().parents[2] / "lem-panel" / "scripts" / "cast.py"
# How many words of each persona's "Who they are" a brief carries. A guess, not a measurement: at
# about 200 words a minute, the part of three or four personas reads in a minute.
WHO_WORDS = 60
WHO_HEADING = re.compile(r"\A#{2,6}\s+who they are\s*\Z", re.IGNORECASE)


class ExpertError(Exception):
    pass


def script(name: str, repo: Path, *args: str) -> str:
    ran = subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / name), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode != 0:
        raise ExpertError(
            ran.stderr.strip().removeprefix(f"{name}: ") or f"{name} {args[0]} failed"
        )
    # a line project.py writes on stderr when it succeeds (the settings read from the base branch) is this script's to say too
    if ran.stderr:
        sys.stderr.write(ran.stderr)
    return ran.stdout


def state_folder(repo: Path) -> Path:
    return Path(script("project.py", repo, "state-dir").strip())


def name_of(model: str) -> str:
    """An expert's name: the last word of its model that holds a letter (`gpt-6-astra` is astra)."""
    words = [
        word for word in re.split(r"[-_.]", model.lower()) if re.search(r"[a-z]", word)
    ]
    return words[-1] if words else model.lower()


def parse_seat(given: str, where: str, place: str | None) -> dict:
    """One `--seat`, as `lem project show` gives a seat of the settings: its parts, each None when
    the seat leaves it out, and its place among the seats."""
    found = SEAT.match(given)
    if found is None:
        raise ExpertError(
            f"{where} {given!r} is no seat: write it as agent/model:effort, for example {EXAMPLE_SEAT}"
        )
    if found["agent"] not in AGENTS:
        raise ExpertError(
            f"{where} {given!r} names the agent {found['agent']!r}: an expert is started by {' or '.join(AGENTS)}, the agents the harness knows"
        )
    return {"seat": found.group(0), **found.groupdict(), "place": place}


def seats(repo: Path, given: list[str]) -> list[dict]:
    """The experts, each with its seat's parts and its place: `--seat` when given, in the order
    given, else the settings' `seats.experts` as `lem project show` resolves them (the project's,
    this machine's own, or Lem's default). Each is named by its model, or by its place."""
    if given:
        experts = [
            parse_seat(seat, "--seat", PLACES[number] if number < len(PLACES) else None)
            for number, seat in enumerate(given)
        ]
    else:
        named = [
            seat
            for seat in json.loads(script("project.py", repo, "show"))["seats"][
                "experts"
            ]
            if seat.get("here", True)
        ]
        if not named:
            raise ExpertError(
                "no expert of the settings' seats.experts can answer on this machine: name a seat of an agent it has, or give --seat"
            )
        experts = [
            {
                key: seat.get(key)
                for key in ("seat", "agent", "model", "effort", "place")
            }
            for seat in named
        ]
    for expert in experts:
        expert["name"] = (
            name_of(expert["model"])
            if expert["model"]
            else expert["place"] or expert["agent"]
        )
    names = [expert["name"] for expert in experts]
    twice = sorted({name for name in names if names.count(name) > 1})
    if twice:
        raise ExpertError(
            f"two experts are named {', '.join(twice)} ({', '.join(e['seat'] for e in experts)}): each answer file carries the name, so give models whose last words differ"
        )
    return experts


def checkout(repo: Path) -> Path:
    ran = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode != 0:
        raise ExpertError(
            f"{repo} is not inside a git checkout: the experts read a checkout, so give --repo one"
        )
    return Path(ran.stdout.strip()).resolve()


def named_files(place: Path, names: list[str], where: str) -> list[Path]:
    files = []
    for name in names:
        path = Path(name) if Path(name).is_absolute() else place / name
        if not path.exists():
            raise ExpertError(
                f"--file {name} is not in {where} ({place}): name a file that matters, relative to it"
            )
        files.append(path.resolve())
    return files


def who_they_are(text: str, stem: str) -> tuple[str, str]:
    """A persona's first heading and its "Who they are" part, as one line of WHO_WORDS words at most,
    cut at the end of a sentence. A file with no such part gives its first paragraph after the
    heading that is not a quote or a comment; a file with no heading is named by its stem."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    lines = text.splitlines()
    heading = next((line[2:].strip() for line in lines if line.startswith("# ")), stem)
    who = next(
        (n + 1 for n, line in enumerate(lines) if WHO_HEADING.match(line.strip())), None
    )
    part: list[str] = []
    if who is not None:
        for line in lines[who:]:
            if line.startswith("#"):
                break
            part.append(line.strip())
    else:
        first = next(
            (n + 1 for n, line in enumerate(lines) if line.startswith("# ")), 0
        )
        for line in lines[first:]:
            bare = line.strip()
            if not bare or bare.startswith("#"):
                if part:
                    break
            elif not bare.startswith(">"):
                part.append(bare)
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(" ".join(part).split()))
    kept: list[str] = []
    for sentence in sentences:
        if kept and len(" ".join([*kept, sentence]).split()) > WHO_WORDS:
            kept.append("…")
            break
        kept.append(sentence)
    return heading, " ".join(kept).strip()


def audience_text(found: dict) -> str:
    """The part of a brief that says who the code is for, from what `lem cast` printed: the
    profile's path and each persona's file, first heading and "Who they are"."""
    profile = found.get("profile")
    read_first = (
        f"The project's profile, `{profile['path']}`, says what the product is and who uses it: read it first."
        if profile
        else "The project has no profile, so the people below are all it says about who uses it."
    )
    people = []
    for persona in found["personas"]:
        heading, who = who_they_are(
            Path(persona.get("person") or persona["path"]).read_text(encoding="utf-8"),
            persona["stem"],
        )
        people.append(
            f"- **{heading}** (`{persona['path']}`): {who or 'the file says who they are.'}"
        )
    listed = "\n".join(people)
    return f"""## Who the code is for

{read_first} The project's personas are the people a change here affects; each file says more:

{listed}

Weigh each option by what it does to these people. You still decide as an engineer: they are
context, and you answer as none of them.
"""


def audience(repo: Path) -> str:
    """Who the code is for, from the project's cast and profile, which the persona panel's script
    finds. A project with no personas has a setup that is not finished, and its brief is refused."""
    ran = subprocess.run(
        [sys.executable, "-B", str(CAST), "--repo", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode != 0:
        said = ran.stderr.strip().removeprefix("cast: ") or "lem cast failed"
        raise ExpertError(
            f"the brief says who the code is for, from the project's personas, and `lem cast` says: {said}"
        )
    try:
        return audience_text(json.loads(ran.stdout))
    except (OSError, UnicodeDecodeError) as error:
        raise ExpertError(
            f"the brief reads each persona's file, and one does not read: {error}"
        ) from error


def answer_form(options: list[str], pick_from: str) -> str:
    if options:
        return f"""    pick: ONE OPTION, COPIED WORD FOR WORD FROM {pick_from}
    why: two to four sentences: what decides it, from the criteria, the plan or the code.

    none fits
    why: two to four sentences: why no option fits, and what would."""
    return """    answer: one to three sentences: your answer to the question.
    why: two to four sentences: what decides it, from the code, the files or what you know."""


# The forms of an answer, with any indent an expert copied from the brief
ANSWER = re.compile(
    r"\A(?:pick:[ \t]*(?P<pick>\S[^\n]*?)|(?P<none>none fits))[ \t]*\n\s*why:[ \t]*(?P<why>\S.*)\Z",
    re.DOTALL | re.IGNORECASE,
)
FREE = re.compile(
    r"\Aanswer:[ \t]*(?P<answer>\S.*?)\n\s*why:[ \t]*(?P<why>\S.*)\Z",
    re.DOTALL | re.IGNORECASE,
)


def read_answer(answer: Path, expert: str, options: bool, one_left: str) -> dict:
    if not answer.is_file():
        raise ExpertError(
            f"{answer} is not there: {expert}'s last message goes into it word for word before it is recorded"
        )
    try:
        written = answer.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ExpertError(
            f"{answer} is not UTF-8 text (byte {error.start} does not read): write {expert}'s last message into it as it came"
        ) from error
    found = (ANSWER if options else FREE).match(written.strip())
    if found is None:
        form = (
            "`pick: OPTION` or `none fits`, then `why: ...`"
            if options
            else "`answer: ...`, then `why: ...`"
        )
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


# --- a question in words --------------------------------------------------------------------


def questions(repo: Path) -> Path:
    return state_folder(repo) / "experts"


def new_folder(top: Path, question: str, at: datetime) -> Path:
    words = (
        "-".join(re.findall(r"[a-z0-9]+", question.lower())[:6])[:48].strip("-")
        or "question"
    )
    stem = f"{at.strftime('%Y-%m-%d-%H%M%S')}-{words}"
    top.mkdir(parents=True, exist_ok=True)
    for n in range(1, 100):
        folder = top / (stem if n == 1 else f"{stem}-{n}")
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            continue
    raise ExpertError(
        f"99 folders named {stem} are in {top}: remove some, then ask again"
    )


def free_brief_text(
    question: str,
    context: str,
    options: list[str],
    place: Path,
    files: list[Path],
    count: int,
    people: str = "",
) -> str:
    decided = (
        f"\n## What is being decided\n\n{context.strip()}\n" if context.strip() else ""
    )
    listed = (
        "\n".join(f"- {file}" for file in files)
        or "- none named: read what the question points at"
    )
    if options:
        offered = (
            "\n## The options, word for word\n\n"
            + "\n".join(f"{n}. {option}" for n, option in enumerate(options, start=1))
            + "\n"
        )
        forms = "one of these two forms"
    else:
        offered = "\nNo options were given: answer the question itself.\n"
        forms = "this form"
    asks = (
        f"The owner asks {count} experts of different model families one question, and each answers it from\nthis brief on their own."
        if count > 1
        else "The owner asks one expert this question, and you answer it from this brief."
    )
    beside = " beside the others'" if count > 1 else ""
    return f"""# A question for the experts

{asks} Your answer goes to the owner{beside}. It decides nothing by itself.

Read only. Change no file, run nothing that writes, and commit nothing. The checkout is
`{place}`.

## The question

{question.strip()}
{decided}{offered}
## The files that matter

{listed}

{people}
## Your answer

Your last message is your answer, in {forms} and nothing else: no heading, no quote marks, no
text before or after.

{answer_form(options, "THE OPTIONS ABOVE")}
"""


def write_record(folder: Path, record: dict) -> None:
    staging = folder / f".record.{os.getpid()}"
    staging.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(staging, folder / "record.json")


def summary(folder: Path, record: dict) -> dict:
    answers = record["answers"]
    picks = {answer.get("pick") for answer in answers.values()}
    shared = (
        picks.pop()
        if record["options"] and len(answers) > 1 and len(picks) == 1
        else None
    )
    waiting = [
        expert["name"] for expert in record["experts"] if expert["name"] not in answers
    ]
    if waiting:
        then = f"wait for {' and '.join(waiting)}; as each ends, `lem experts record --folder {folder.name} --expert NAME`"
    elif record["options"]:
        then = (
            "show the owner the answers side by side, "
            + (f"all picked {shared!r}" if shared else "where they split")
            + ", and one line of what you would do with them"
        )
    else:
        then = "show the owner the answers side by side, where they agree and where they split, and one line of what you would do with them"
    return {
        "folder": folder.name,
        "dir": str(folder),
        **record,
        "agree": shared,
        "waiting": waiting,
        "next": then,
    }


def cmd_free_brief(
    repo: Path,
    question: str,
    context: str,
    options: list[str],
    names: list[str],
    given: list[str],
) -> dict:
    if not question.strip():
        raise ExpertError("--question is empty: give the question in words")
    if len(set(options)) != len(options):
        raise ExpertError("two --option are the same text: give each option once")
    if len(options) == 1:
        raise ExpertError(
            "one --option is no choice: give two or more, or none for an open question"
        )
    experts = seats(repo, given)
    place = checkout(repo)
    files = named_files(place, names, "the checkout")
    who = audience(repo)
    top = questions(repo)
    now = datetime.now(timezone.utc)
    folder = new_folder(top, question, now)
    (folder / "brief.md").write_text(
        free_brief_text(question, context, options, place, files, len(experts), who),
        encoding="utf-8",
    )
    record = {
        "question": question.strip(),
        "context": context.strip(),
        "options": options,
        "files": [str(file) for file in files],
        "asked": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checkout": str(place),
        "experts": [
            {**expert, "answer": str(folder / f"{expert['name']}.md")}
            for expert in experts
        ],
        "answers": {},
    }
    write_record(folder, record)
    names_ = [expert["name"] for expert in experts]
    return {
        "folder": folder.name,
        "dir": str(folder),
        "brief": str(folder / "brief.md"),
        "worktree": str(place),
        "experts": record["experts"],
        "answers": {expert["name"]: expert["answer"] for expert in record["experts"]},
        "ask": names_,
        "next": f"start {' and '.join(names_)} at once, in the background, with this brief (the harness's `ask-experts`); "
        f"as each ends, `lem experts record --folder {folder.name} --expert NAME`",
    }


def cmd_free_record(repo: Path, name: str, expert: str) -> dict:
    if not FOLDER.match(name):
        raise ExpertError(
            f"--folder {name!r} is no question's folder: give the name `lem experts brief --question` printed"
        )
    folder = questions(repo) / name
    if not (folder / "record.json").is_file():
        raise ExpertError(
            f"no question {name} is in {folder.parent}: give the name `lem experts brief --question` printed; a folder goes state.keep_days days after its last write"
        )
    with open(folder / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        names = [e["name"] for e in record["experts"]]
        if expert not in names:
            raise ExpertError(
                f"--expert {expert} is none of this question's experts ({', '.join(names)})"
            )
        if expert in record["answers"]:
            raise ExpertError(
                f"{expert} answered question {name} already: its answer is in {folder / 'record.json'}"
            )
        got = read_answer(
            folder / f"{expert}.md",
            expert,
            options=bool(record["options"]),
            one_left="the owner then has the other experts' answers only",
        )
        if "pick" in got and got["pick"] not in record["options"]:
            raise ExpertError(
                f"the pick of an expert is one of the options, word for word: {'; '.join(record['options'])}; {got['pick']!r} is none of them"
            )
        record["answers"][expert] = {
            **got,
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        write_record(folder, record)
    return summary(folder, record)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lem experts",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="a directory inside the checkout (default: the current one)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    brief = commands.add_parser("brief")
    brief.add_argument(
        "--question",
        required=True,
        help="a question in words, which has a folder of its own",
    )
    brief.add_argument(
        "--context", default="", help="what is being decided, and why it came up"
    )
    brief.add_argument(
        "--option",
        action="append",
        default=[],
        help="an option, word for word, once for each",
    )
    brief.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="PATH",
        help="a file that matters, relative to the checkout --repo names",
    )
    record = commands.add_parser("record")
    record.add_argument(
        "--folder",
        required=True,
        help="the folder of a question in words, as brief printed it",
    )
    record.add_argument("--expert", required=True)
    for each in (brief, record):
        each.add_argument(
            "--seat",
            action="append",
            default=[],
            metavar="AGENT/MODEL:EFFORT",
            help="an expert, once for each, in the place of the settings' seats.experts",
        )
    args = parser.parse_args()
    for arg in sys.argv[1:]:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            sys.exit(
                f"experts.py: the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8"
            )
    repo = Path(args.repo)
    try:
        if args.command == "brief":
            result = cmd_free_brief(
                repo, args.question, args.context, args.option, args.file, args.seat
            )
        else:
            if args.seat:
                raise ExpertError(
                    "--seat belongs to brief: a question's experts are the ones its brief named"
                )
            result = cmd_free_record(repo, args.folder, args.expert)
    except ExpertError as error:
        sys.exit(f"experts.py: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

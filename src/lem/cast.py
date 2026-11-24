#!/usr/bin/env python3
"""Find a persona panel's cast, copy it into a project, and make the folder a panel
writes in.

Usage: lem cast [--repo DIR]
       lem cast init [--repo DIR]
       lem cast run-dir SLUG [--repo DIR]

With no command it prints the cast as JSON: the layer it came from, where in that layer
(`source`), its directory, its index (README.md, or null), each persona, and the
project's profile (`profile`: its path and source, or null). A cast is a folder with any
persona file, a `*.md` other than README.md, and a panel has one source of it:

  project   the personas path of the project's settings (.lem/personas/ unless they say
            otherwise) in the checkout, or else on the repository's default branch

Every project that uses Lem has personas: its onboarding writes them. A project with
none has a setup that is not finished, so this command exits 1 and names the step that
writes them. Generic people do not stand in: a panel of them answers for nobody the
project named.

One more folder holds a cast, and it never answers a panel: the built-in cast shipped
beside this script, which `init` copies as a first cast for a project that has none yet.

A checkout with no cast of its own may still belong to a project that has one: a
worktree branched before the cast landed, or moved. A checkout whose cast is an
unchanged older copy (the branch never edited it, and the default branch has moved on)
reads the default branch's too; a branch that edits its cast keeps its own. Its panel
reads the default branch's cast, never a generic one, so a session running in that
worktree keeps the project's people without a rebase. Of the local and remote default
branch, the newer one is read: work can land on either side first. The files are written
once per commit in Lem's state folder (`.lem/state/personas-cast/<sha>/` of the main
checkout, as `state.py` names it), which git never shows and every worktree shares;
`source` names the branch and commit. Each read writes its time on the copy it reads,
here and for the copies of the profile and of a persona below, and `lem project prune`
removes a copy that nobody wrote or read for `state.keep_days` days.

The profile, at the settings' profile path (.lem/profile.md unless they say otherwise),
says what the project is: the product, its scale, its rules and the teams it compares
itself with. Every persona, the practice scout and the moderator read it first. It has
one layer, the project's: a profile is about one project, so no other profile stands in
for it. A checkout without one reads the default branch's, as for the cast, written in
the state folder (personas-profile/<blob id>.md, one file per version of the profile);
with neither, `profile` is null.

Each persona is its stem, its file (`path`), and what the panel starts it with:

  seats       the seats it answers on, each `seat` (`agent/model:effort`), `agent`, `model`,
              `effort` (null when the seat leaves it out) and `name`, which its answer files carry
  left_out    its seats whose agent is not on this machine (a `codex` seat without Codex)
  seats_from  `file` when its file names them, or `default`: once on Opus and once on the paired
              Codex's `persona` agent (`opus` and `sol`), as every panel ran before
  person      the file its agent reads as who it is: the file itself, or, when the file has a
              frontmatter, its text without it, written once in the state folder (personas-person/)

A persona's file names its seats in a frontmatter, each as the settings write a seat,
and nothing else is in it:

  ---
  seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]
  ---

A seat that the settings would refuse, a key that is not `seats` and a frontmatter that
is never closed stop the command with the file and the line to write.

`init` copies the built-in cast into the project's personas folder so the project has
its own people to rewrite. It refuses a checkout whose personas folder already holds any
file, and one whose default branch already has a cast, which a rebase brings in instead.

`run-dir` makes panels/<YYYY-MM-DD>-<SLUG>/ in Lem's state folder (`.lem/state/panels/`
of the main checkout) and prints its path. Git never shows the state folder, so a
panel's files never show in `git status` and a project needs no ignore rule of its own;
a worktree's removal does not take them, and `lem project prune` removes the folder
`state.keep_days` days after its last write. An existing folder is refused, so two
panels never write into one.
"""  # noqa: E501 - the table of a persona's keys keeps its columns

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import typing
from collections.abc import Callable
from pathlib import Path

# project: the one reader of a seat, `agent/model:effort`, and whether its agent is here
from lem import paths, project

# `lem_state` is the one place that says where the state is.
from lem import state as lem_state

# Where a project keeps its personas and its profile, relative to the checkout: each has
# one place, which configure() takes from `project.py show` (`places`).
PROJECT_CAST = Path(".lem") / "personas"
PROJECT_PROFILE = Path(".lem") / "profile.md"
# The folder of Lem's state folder that holds each panel's own folder.
PANELS = "panels"
BUILT_IN = paths.CAST

# A persona's own seats, in the frontmatter of its file: the one key, the agents that
# can answer as a persona, and the line to write.
SEATS_KEY = "seats"
PERSONA_AGENTS = ("claude", "codex")
SEATS_LINE = 'seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]'
# The seats of a persona whose file names none: the panel as it ran before a persona
# could name its own, once on Opus and once on the other family through the paired
# Codex's `persona` agent, whose model that agent's own definition names. Their names
# are the answer files' (`<stem>.opus.md`, `<stem>.sol.md`).
DEFAULT_SEATS: tuple[dict[str, typing.Any], ...] = (
    {
        "seat": "claude/opus",
        "agent": "claude",
        "model": "opus",
        "effort": None,
        "name": "opus",
    },
    {"seat": "codex", "agent": "codex", "model": None, "effort": None, "name": "sol"},
)


class CastError(Exception):
    pass


def frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    """A persona file's frontmatter, as its keys and their raw values, and the file
    without it.

    A file whose first line is `---` opens one, and the next `---` line closes it. Each
    line inside is `key: value`; a blank line and a `#` comment are skipped. A file with
    no frontmatter gives {} and its whole text."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return {}, text
    end = next(
        (
            n
            for n, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if end is None:
        raise CastError(
            f"{path} opens a frontmatter with `---` on its first line and no `---` "
            "line closes it: close it, or take the first line out"
        )
    meta: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        bare = line.strip()
        if not bare or bare.startswith("#"):
            continue
        key, colon, value = bare.partition(":")
        key = key.strip()
        if not colon or not key:
            raise CastError(
                f"{path}, line {number}: {bare!r} is no `key: value` line; "
                f"a persona's frontmatter holds one line, {SEATS_LINE}"
            )
        if key != SEATS_KEY:
            raise CastError(
                f"{path}, line {number}: the frontmatter of a persona knows only "
                f"`{SEATS_KEY}`, not {key!r}; write {SEATS_LINE}, or take the line out"
            )
        if key in meta:
            raise CastError(
                f"{path}, line {number}: `{key}` is written twice; "
                f"keep one line, {SEATS_LINE}"
            )
        meta[key] = value.strip()
    return meta, "".join(lines[end + 1 :]).lstrip("\r\n")


def seat_name(seat: dict) -> str:
    """A seat's name, which its answer files carry: the last word of its model that
    holds a letter (`gpt-6.2-sol` is sol), or its agent when it names no model; the
    experts' names follow the same rule."""
    if not seat["model"]:
        return seat["agent"]
    words = [
        word
        for word in re.split(r"[-_.]", seat["model"].lower())
        if re.search(r"[a-z]", word)
    ]
    return words[-1] if words else seat["model"].lower()


def seats_of(
    meta: dict[str, str],
    path: Path,
    here: Callable[[str], bool] = project.agent_here,
) -> dict[str, object]:
    """The seats a persona answers on: its file's `seats`, each checked as a seat of the
    settings is, or the panel's DEFAULT_SEATS when its file names none. A seat whose
    agent is not on this machine (`here`) is left out, as the panel leaves out its
    second family without Codex."""
    raw = meta.get(SEATS_KEY)
    if raw is None:
        named, source = [dict(seat) for seat in DEFAULT_SEATS], "default"
    else:
        try:
            given = json.loads(raw)
        except ValueError:
            given = None
        if not isinstance(given, list) or not given:
            raise CastError(
                f"{path}: seats: {raw} is not a list of one seat or more in double "
                f"quotes: write {SEATS_LINE}, or take the line out for "
                "the panel's own two seats"
            )
        named, source = [], "file"
        for number, text in enumerate(given):
            try:
                seat = project.parse_seat(
                    text,
                    f"{path}: seats[{number}]",
                    PERSONA_AGENTS,
                    "the agents a persona is started with",
                    "claude/opus:high",
                )
            except project.SettingsError as error:
                raise CastError(f"{error}. The line is {SEATS_LINE}") from error
            named.append({**seat, "name": seat_name(seat)})
        names = [seat["name"] for seat in named]
        twice = sorted({name for name in names if names.count(name) > 1})
        if twice:
            raise CastError(
                f"{path}: two seats are named {', '.join(twice)} "
                f"({', '.join(seat['seat'] for seat in named)}): each answer file "
                "carries the last word of its seat's model, "
                "so give models whose last words differ"
            )
    return {
        "seats": [{**seat, "here": True} for seat in named if here(seat["agent"])],
        "left_out": [
            {**seat, "here": False} for seat in named if not here(seat["agent"])
        ],
        "seats_from": source,
    }


def persona(
    root: Path, path: Path, here: Callable[[str], bool] = project.agent_here
) -> dict[str, object]:
    """One persona as the panel reads it: its stem and file, its seats, and `person`,
    the file a persona's agent reads as who it is: the file itself, or, when it has a
    frontmatter, its text without it, written once in Lem's state folder."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise CastError(
            f"{path} is not UTF-8 text (byte {error.start} does not read): "
            "save it as UTF-8"
        ) from error
    meta, body = frontmatter(text, path)
    found = {"stem": path.stem, "path": str(path), **seats_of(meta, path, here)}
    if body == text:
        return {**found, "person": str(path)}
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return {
        **found,
        "person": str(
            state_file(
                root,
                "personas-person",
                f"{path.stem}-{digest}.md",
                body.encode("utf-8"),
            )
        ),
    }


def fail(message: str) -> typing.NoReturn:
    print(f"cast: {message}", file=sys.stderr)
    sys.exit(1)


def configure(root: Path) -> None:
    """Take the places of the personas and the profile from the project's settings,
    which this checks first: a settings file that does not read stops the panel."""
    global PROJECT_CAST, PROJECT_PROFILE  # noqa: PLW0603 - the places hold for the whole run, and every reader takes them from here
    done = subprocess.run(
        [sys.executable, "-B", str(paths.MAIN), "project", "--repo", str(root), "show"],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        fail(done.stderr.strip() or "could not read the project's settings")
    settings = json.loads(done.stdout)
    top = Path(settings["root"]).resolve()
    PROJECT_CAST = Path(settings["places"]["personas"]["path"]).relative_to(top)
    PROJECT_PROFILE = Path(settings["places"]["profile"]["path"]).relative_to(top)


def git(cwd: Path, *args: str) -> str:
    done = lem_state.run_git(cwd, list(args))
    return done.stdout.strip() if done.returncode == 0 else ""


def cache(root: Path, folder: str) -> Path:
    """The folder `folder` of the panel's copies in Lem's state folder."""
    try:
        return lem_state.folder(root) / folder
    except lem_state.StateError as error:
        fail(str(error))
        raise AssertionError from error


def checkout_root(start: Path) -> Path:
    if not start.is_dir():
        fail(f"{start} is not a directory")
    top = git(start, "rev-parse", "--show-toplevel")
    return Path(top) if top else start.resolve()


def is_persona(name: str) -> bool:
    return name.endswith(".md") and Path(name).name != "README.md"


def personas(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.md") if is_persona(p.name))


def commit_of(root: Path, ref: str) -> str:
    return git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")


def default_refs(root: Path) -> list[str]:
    """The default branch's local and remote refs that exist, the newer first.

    Work can land on either side first: a commit on the local branch waits for its push,
    and a worktree that pushes straight to the remote leaves the local branch behind
    until someone fast-forwards it. When one contains the other, the containing one is
    read first; when they have diverged, the local one is.
    """
    remote_head = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    names = (
        [remote_head.removeprefix("refs/remotes/origin/")]
        if remote_head
        else ["master", "main", "trunk"]
    )
    refs: list[str] = []
    for name in names:
        local, upstream = f"refs/heads/{name}", f"refs/remotes/origin/{name}"
        pair = [ref for ref in (local, upstream) if commit_of(root, ref)]
        if pair == [local, upstream] and commit_of(root, local) != commit_of(
            root, upstream
        ):
            local_is_behind = (
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(root),
                        "merge-base",
                        "--is-ancestor",
                        local,
                        upstream,
                    ],
                    check=False,
                ).returncode
                == 0
            )
            if local_is_behind:
                pair.reverse()
        refs += pair
    return refs


def default_branch_cast(root: Path) -> tuple[str, Path, str] | None:
    """The default branch's cast, written out in the state folder, with the ref it came
    from, or None when it has none."""
    for ref in default_refs(root):
        sha = commit_of(root, ref)
        label = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
        listed = git(
            root, "ls-tree", "--name-only", sha, "--", f"{PROJECT_CAST.as_posix()}/"
        )
        names = [n for n in listed.splitlines() if n.endswith(".md")]
        if not any(is_persona(n) for n in names):
            continue
        target = cache(root, "personas-cast") / sha
        if not target.is_dir():
            # Two sessions may resolve the same commit at once: each stages under its
            # own name and the first rename wins; the loser's copy is identical, so it
            # is dropped.
            staging = target.with_name(f"{sha}.{os.getpid()}.partial")
            staging.mkdir(parents=True)
            for name in names:
                body = subprocess.run(
                    ["git", "-C", str(root), "show", f"{sha}:{name}"],
                    capture_output=True,
                    check=False,
                )
                if body.returncode:
                    fail(
                        f"could not read {name} at {label} ({sha[:9]}): "
                        f"{body.stderr.decode().strip()}"
                    )
                (staging / Path(name).name).write_bytes(body.stdout)
            try:
                staging.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
                shutil.rmtree(staging)
        else:
            read_now(target)
        return f"{label} at {sha[:9]}", target, ref
    return None


def follows_default(root: Path, ref: str, path: str) -> bool:
    """Whether this checkout left path as the default branch had it and that branch has
    moved on.

    True when the checkout neither committed a change to path since its merge base with
    ref nor holds one uncommitted, and ref's version differs from HEAD's: the checkout's
    copy is then only an older version of the default branch's. A branch that edits path
    keeps its own.
    """
    base = git(root, "merge-base", "HEAD", ref)
    if not base:
        return False
    committed = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", base, "HEAD", "--", path],
        check=False,
    ).returncode
    pending = git(root, "status", "--porcelain", "--untracked-files=all", "--", path)
    if committed or pending:
        return False
    return git(root, "rev-parse", f"HEAD:{path}") != git(
        root, "rev-parse", f"{ref}:{path}"
    )


def state_file(root: Path, folder: str, name: str, body: bytes) -> Path:
    """Write body once to <state folder>/<folder>/<name> and return the path.

    Two sessions may write the same commit's file at once: each stages under its own
    name and the first rename wins; the copies are identical, so the loser's is dropped.
    """
    target = cache(root, folder) / name
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = target.with_name(f"{name}.{os.getpid()}.partial")
        staging.write_bytes(body)
        try:
            staging.rename(target)
        except OSError:
            if not target.is_file():
                raise
            staging.unlink()
    else:
        read_now(target)
    return target


def read_now(copy: Path) -> None:
    """Write the time of this read on a copy in the state folder: `lem project prune`
    removes a copy by its last write, so a copy a panel still reads stays. A copy that
    cannot take the time is read all the same."""
    with contextlib.suppress(OSError):
        os.utime(copy)


def profile(root: Path) -> dict[str, str] | None:
    """The project's profile: the checkout's, else the default branch's, else None.

    A checkout whose profile is only an older copy of the default branch's reads the
    default branch's, so an edit to the profile reaches every worktree without a merge.
    """
    local = root / PROJECT_PROFILE
    for ref in default_refs(root):
        sha = commit_of(root, ref)
        label = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
        there = PROJECT_PROFILE.as_posix()
        if git(root, "cat-file", "-t", f"{sha}:{there}") != "blob":
            continue
        if local.is_file() and not follows_default(
            root, ref, PROJECT_PROFILE.as_posix()
        ):
            break
        body = subprocess.run(
            ["git", "-C", str(root), "show", f"{sha}:{there}"],
            capture_output=True,
            check=False,
        )
        if body.returncode:
            fail(
                f"could not read {there} at {label} ({sha[:9]}): "
                f"{body.stderr.decode().strip()}"
            )
        # Named by the file's own blob id, so every commit that leaves the profile
        # unchanged reuses one copy instead of adding another.
        blob = git(root, "rev-parse", f"{sha}:{there}")
        path = state_file(root, "personas-profile", f"{blob}.md", body.stdout)
        return {"source": f"{label} at {sha[:9]}", "path": str(path)}
    if local.is_file():
        return {"source": "checkout", "path": str(local)}
    return None


def resolve(root: Path) -> dict[str, object]:
    # A checkout whose cast is only an older copy of the default branch's reads the
    # default branch's, so a new persona reaches every worktree without a merge.
    found_cast = project_cast(root)
    if found_cast is None:
        fail(
            f"this project has no personas in {PROJECT_CAST}, so its setup is not "
            "finished and no panel can run: `/lem init` writes them from the owner's "
            "answers, or `lem cast init` copies a starting cast there for him to "
            "rewrite. No generic cast answers in their place",
        )
        raise AssertionError
    # each persona's seats and the text its agent reads, from the files of the cast that
    # was found
    try:
        # pick() lists the personas as a list of records
        listed = typing.cast("list[dict[str, object]]", found_cast["personas"])
        found_cast["personas"] = [
            persona(root, Path(str(one["path"]))) for one in listed
        ]
    except CastError as error:
        fail(str(error))
    return found_cast


def starting(root: Path) -> dict[str, object]:
    """Where `init` copies a first cast from: the cast shipped beside this script, and
    nothing else."""
    found = pick(root, [("built-in", "panel", BUILT_IN)])
    if found is None:
        fail(
            "no persona files to start from; the built-in cast at "
            f"{BUILT_IN} is missing"
        )
        raise AssertionError
    return found


def pick(
    root: Path, candidates: list[tuple[str, str, Path]]
) -> dict[str, object] | None:
    for layer, source, directory in candidates:
        found_personas = personas(directory)
        if found_personas:
            index = directory / "README.md"
            return {
                "layer": layer,
                "source": source,
                "dir": str(directory),
                "index": str(index) if index.is_file() else None,
                "personas": [{"stem": p.stem, "path": str(p)} for p in found_personas],
                "profile": profile(root),
            }
    return None


def project_cast(root: Path) -> dict[str, object] | None:
    """The project's own cast, from the checkout or the default branch, or None when it
    wrote none."""
    candidates: list[tuple[str, str, Path]] = []
    found = default_branch_cast(root)
    local = bool(personas(root / PROJECT_CAST))
    if found and (
        not local or follows_default(root, found[2], PROJECT_CAST.as_posix())
    ):
        candidates.append(("project", found[0], found[1]))
    candidates.append(("project", "checkout", root / PROJECT_CAST))
    return pick(root, candidates)


def init(root: Path) -> None:
    target = root / PROJECT_CAST
    if target.is_dir() and any(target.iterdir()):
        fail(f"{target} already holds files; edit them there")
    there = project_cast(root)
    if there is not None:
        fail(
            f"the default branch already has a cast ({there['source']}); "
            "rebase onto it instead"
        )
    cast = starting(root)
    source = Path(str(cast["dir"]))
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.md")):
        shutil.copy2(path, target / path.name)
    print(f"copied the {cast['layer']} cast from {source} to {target}")


def run_dir(root: Path, slug: str) -> None:
    if not slug or "/" in slug or slug.startswith((".", "-")):
        fail(f"a slug is one plain path segment, not {slug!r}")
    panels = cache(root, PANELS)
    panels.mkdir(exist_ok=True)
    target = panels / f"{dt.date.today().isoformat()}-{slug}"  # noqa: DTZ011 - a panel's folder is named for the owner's local day
    if target.exists():
        fail(f"{target} already exists; add a suffix such as -2 to the slug")
    target.mkdir()
    print(target)


def main(argv: list[str]) -> None:
    repo = Path.cwd()
    if "--repo" in argv:
        at = argv.index("--repo")
        if at + 1 >= len(argv):
            fail("--repo needs a directory")
        repo = Path(argv[at + 1])
        argv = argv[:at] + argv[at + 2 :]
    root = checkout_root(repo)
    configure(root)
    if not argv:
        print(json.dumps(resolve(root), indent=2))
    elif argv == ["init"]:
        init(root)
    elif argv[:-1] == ["run-dir"]:
        run_dir(root, argv[1])
    else:
        fail(f"unexpected arguments {argv!r}; see the usage in this script's docstring")


if __name__ == "__main__":
    main(sys.argv[1:])

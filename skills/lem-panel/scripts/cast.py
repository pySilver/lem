#!/usr/bin/env python3
"""Find a persona panel's cast, copy it into a project, and make the folder a panel writes in.

Usage: cast.py [--repo DIR]
       cast.py init [--repo DIR]
       cast.py run-dir SLUG [--repo DIR]

With no command it prints the cast as JSON: the layer it came from, where in that layer (`source`),
its directory, its index (README.md, or null), each persona's stem and path, and the project's
profile (`profile`: its path and source, or null). A cast is a folder with any persona file, a
`*.md` other than README.md, and a panel has one source of it:

  project   the personas path of the project's settings (.lem/personas/ unless they say
            otherwise) in the checkout, or else on the repository's default branch

A project that wrote no personas has no panel: `layer` is null, `personas` is empty and `why`
says so, with exit 0, because that is an answer and not a fault. The one who asked then puts the
question to the owner as it is. Generic people do not stand in: a panel of them answers for
nobody the project named, and the owner of such a project chose to get his questions at once.

Two more folders hold a cast, and neither ever answers a panel. They are where `init` copies a
first cast from, for a project whose owner wants personas:

  user      ~/.config/personas/cast/
  built-in  the cast shipped beside this script

A checkout with no cast of its own may still belong to a project that has one: a worktree branched
before the cast landed, or moved. A checkout whose cast is an unchanged older copy (the branch never
edited it, and the default branch has moved on) reads the default branch's too; a branch that edits
its cast keeps its own. Its panel reads the default branch's cast, never a generic one, so
a session running in that worktree keeps the project's people without a rebase. Of the local and
remote default branch, the newer one is read: work can land on either side first. The files
are written once per commit under the repository's git directory (personas-cast/<sha>/), which is
never committed and is shared by every worktree; `source` names the branch and commit.

The profile, at the settings' profile path (.lem/profile.md unless they say otherwise), says
what the project is: the product, its scale, its rules and
the teams it compares itself with. Every persona, the practice scout and the moderator read it first.
It has one layer, the project's: a profile is about one project, so no user or built-in profile
stands in for it. A checkout without one reads the default branch's, as for the cast, written under
the git directory (personas-profile/<blob id>.md, one file per version of the profile); with
neither, `profile` is null.

`init` copies a starting cast, the user's or else the built-in one, into the project's personas
folder so the project has its own people to rewrite. It refuses a checkout whose personas folder already holds any file, and one whose default branch
already has a cast, which a rebase brings in instead.

`run-dir` makes runs/<YYYY-MM-DD>-<SLUG>/ beside the personas folder and prints its path. The runs folder holds a
.gitignore of `*`, which ignores the folder and itself, so a panel's files never show in
`git status` and a project needs no ignore rule of its own. An existing folder is refused, so
two panels never write into one.
"""

# The macOS system python3 (3.9) may run this; it needs this for `str | None`.
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Where a project keeps its personas, its profile and its panels' files, relative to the checkout.
# These are Lem's own layout; configure() replaces them with what the project's
# settings say, so a project that keeps its cast where an older tool reads it is served too.
PROJECT_CAST = Path(".lem") / "personas"
PROJECT_PROFILE = Path(".lem") / "profile.md"
# Lem's own layout, which a settings file that names no path keeps.
LAYOUT = {"personas": PROJECT_CAST, "profile": PROJECT_PROFILE}
RUNS = Path(".lem") / "runs"
BUILT_IN = Path(__file__).resolve().parent.parent / "cast"
PROJECT_SETTINGS = Path(__file__).resolve().parents[2] / "lem" / "scripts" / "project.py"


def fail(message: str) -> None:
    print(f"cast: {message}", file=sys.stderr)
    sys.exit(1)


def configure(root: Path) -> None:
    """Take the personas and profile paths from the project's settings (.lem/project.toml)."""
    global PROJECT_CAST, PROJECT_PROFILE, RUNS
    done = subprocess.run(
        [sys.executable, "-B", str(PROJECT_SETTINGS), "--repo", str(root), "show"], capture_output=True, text=True
    )
    if done.returncode != 0:
        fail(done.stderr.strip() or "could not read the project's settings")
    settings = json.loads(done.stdout)
    top = Path(settings["root"]).resolve()
    PROJECT_CAST = Path(settings["paths"]["personas"]["path"]).relative_to(top)
    PROJECT_PROFILE = Path(settings["paths"]["profile"]["path"]).relative_to(top)
    RUNS = PROJECT_CAST.parent / "runs"


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


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

    Work can land on either side first: a commit on the local branch waits for its push, and a
    worktree that pushes straight to the remote leaves the local branch behind until someone
    fast-forwards it. When one contains the other, the containing one is read first; when they have
    diverged, the local one is.
    """
    remote_head = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    names = [remote_head.removeprefix("refs/remotes/origin/")] if remote_head else ["master", "main", "trunk"]
    refs: list[str] = []
    for name in names:
        local, upstream = f"refs/heads/{name}", f"refs/remotes/origin/{name}"
        pair = [ref for ref in (local, upstream) if commit_of(root, ref)]
        if len(pair) == 2 and commit_of(root, local) != commit_of(root, upstream):
            local_is_behind = subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", local, upstream],
            ).returncode == 0
            if local_is_behind:
                pair.reverse()
        refs += pair
    return refs


def path_at(root: Path, sha: str, name: str, fallback: Path) -> Path:
    """Where a commit's own settings keep the personas or the profile: this checkout may be older than
    the settings on the default branch, and would look for them in the wrong folder.

    With no settings file at that commit, the checkout's own configured path stands. With one, the
    answer is that file's: the path it names, or Lem's own layout when it names none.
    """
    body = subprocess.run(["git", "-C", str(root), "show", f"{sha}:.lem/project.toml"], capture_output=True, text=True)
    if body.returncode != 0:
        return fallback
    try:
        import tomllib
    except ImportError:
        fail(f"the default branch keeps settings, and this python3 ({sys.version.split()[0]}) cannot read them; run this with Python 3.11 or newer")
        raise AssertionError
    try:
        named = tomllib.loads(body.stdout).get("paths", {}).get(name)
    except (tomllib.TOMLDecodeError, AttributeError) as error:
        fail(f".lem/project.toml at {sha[:9]} does not read ({error}); correct it on the default branch")
        raise AssertionError
    return Path(named.rstrip("/")) if isinstance(named, str) and named.strip() else LAYOUT[name]


def default_branch_cast(root: Path) -> tuple[str, Path] | None:
    """The default branch's cast, written out under the git directory, or None when it has none."""
    for ref in default_refs(root):
        sha = commit_of(root, ref)
        label = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
        listed = git(root, "ls-tree", "--name-only", sha, "--", f"{path_at(root, sha, 'personas', PROJECT_CAST).as_posix()}/")
        names = [n for n in listed.splitlines() if n.endswith(".md")]
        if not any(is_persona(n) for n in names):
            continue
        common = Path(git(root, "rev-parse", "--git-common-dir"))
        target = (common if common.is_absolute() else root / common).resolve() / "personas-cast" / sha
        if not target.is_dir():
            # Two sessions may resolve the same commit at once: each stages under its own name and
            # the first rename wins; the loser's copy is identical, so it is dropped.
            staging = target.with_name(f"{sha}.{os.getpid()}.partial")
            staging.mkdir(parents=True)
            for name in names:
                body = subprocess.run(["git", "-C", str(root), "show", f"{sha}:{name}"], capture_output=True)
                if body.returncode:
                    fail(f"could not read {name} at {label} ({sha[:9]}): {body.stderr.decode().strip()}")
                (staging / Path(name).name).write_bytes(body.stdout)
            try:
                staging.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
                shutil.rmtree(staging)
        return f"{label} at {sha[:9]}", target, ref
    return None


def follows_default(root: Path, ref: str, path: str) -> bool:
    """Whether this checkout left path as the default branch had it and that branch has moved on.

    True when the checkout neither committed a change to path since its merge base with ref nor
    holds one uncommitted, and ref's version differs from HEAD's: the checkout's copy is then only
    an older version of the default branch's. A branch that edits path keeps its own.
    """
    base = git(root, "merge-base", "HEAD", ref)
    if not base:
        return False
    committed = subprocess.run(["git", "-C", str(root), "diff", "--quiet", base, "HEAD", "--", path]).returncode
    pending = git(root, "status", "--porcelain", "--untracked-files=all", "--", path)
    if committed or pending:
        return False
    return git(root, "rev-parse", f"HEAD:{path}") != git(root, "rev-parse", f"{ref}:{path}")


def git_dir_file(root: Path, folder: str, name: str, body: bytes) -> Path:
    """Write body once to <git common dir>/<folder>/<name> and return the path.

    Two sessions may write the same commit's file at once: each stages under its own name and the
    first rename wins; the copies are identical, so the loser's is dropped.
    """
    common = Path(git(root, "rev-parse", "--git-common-dir"))
    target = (common if common.is_absolute() else root / common).resolve() / folder / name
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
    return target


def profile(root: Path) -> dict[str, str] | None:
    """The project's profile: the checkout's, else the default branch's, else None.

    A checkout whose profile is only an older copy of the default branch's reads the default
    branch's, so an edit to the profile reaches every worktree without a merge.
    """
    local = root / PROJECT_PROFILE
    for ref in default_refs(root):
        sha = commit_of(root, ref)
        label = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
        there = path_at(root, sha, "profile", PROJECT_PROFILE).as_posix()
        if git(root, "cat-file", "-t", f"{sha}:{there}") != "blob":
            continue
        if local.is_file() and not follows_default(root, ref, PROJECT_PROFILE.as_posix()):
            break
        body = subprocess.run(
            ["git", "-C", str(root), "show", f"{sha}:{there}"], capture_output=True
        )
        if body.returncode:
            fail(f"could not read {there} at {label} ({sha[:9]}): {body.stderr.decode().strip()}")
        # Named by the file's own blob id, so every commit that leaves the profile unchanged reuses
        # one copy instead of adding another.
        blob = git(root, "rev-parse", f"{sha}:{there}")
        path = git_dir_file(root, "personas-profile", f"{blob}.md", body.stdout)
        return {"source": f"{label} at {sha[:9]}", "path": str(path)}
    if local.is_file():
        return {"source": "checkout", "path": str(local)}
    return None


def resolve(root: Path) -> dict[str, object]:
    # A checkout whose cast is only an older copy of the default branch's reads the default
    # branch's, so a new persona reaches every worktree without a merge.
    candidates: list[tuple[str, str, Path]] = []
    found = default_branch_cast(root)
    local = bool(personas(root / PROJECT_CAST))
    if found and (not local or follows_default(root, found[2], PROJECT_CAST.as_posix())):
        candidates.append(("project", found[0], found[1]))
    candidates.append(("project", "checkout", root / PROJECT_CAST))
    return pick(root, candidates) or {
        "layer": None, "source": None, "dir": None, "index": None, "personas": [], "profile": profile(root),
        "why": "this project wrote no personas, so no panel runs here: put the question to the owner as it is. "
               "`cast.py init` copies a starting cast into the project when the owner wants personas",
    }


def starting(root: Path) -> dict[str, object]:
    """Where `init` copies a first cast from: the user's own, or the one shipped beside this script."""
    found = pick(root, [
        ("user", "~/.config/personas/cast", Path.home() / ".config" / "personas" / "cast"),
        ("built-in", "panel", BUILT_IN),
    ])
    if found is None:
        fail(f"no persona files to start from; the built-in cast at {BUILT_IN} is missing")
        raise AssertionError
    return found


def pick(root: Path, candidates: list[tuple[str, str, Path]]) -> dict[str, object] | None:
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


def init(root: Path) -> None:
    target = root / PROJECT_CAST
    if target.is_dir() and any(target.iterdir()):
        fail(f"{target} already holds files; edit them there")
    if resolve(root)["layer"] == "project":
        fail(f"the default branch already has a cast ({resolve(root)['source']}); rebase onto it instead")
    cast = starting(root)
    source = Path(str(cast["dir"]))
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.md")):
        shutil.copy2(path, target / path.name)
    print(f"copied the {cast['layer']} cast from {source} to {target}")


def run_dir(root: Path, slug: str) -> None:
    if not slug or "/" in slug or slug.startswith(".") or slug.startswith("-"):
        fail(f"a slug is one plain path segment, not {slug!r}")
    runs = root / RUNS
    runs.mkdir(parents=True, exist_ok=True)
    ignore = runs / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n")
    target = runs / f"{datetime.date.today().isoformat()}-{slug}"
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
    elif len(argv) == 2 and argv[0] == "run-dir":
        run_dir(root, argv[1])
    else:
        fail(f"unexpected arguments {argv!r}; see the usage in this script's docstring")


if __name__ == "__main__":
    main(sys.argv[1:])

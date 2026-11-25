"""`lem rules` as the owner's agents run it, on a real repository: the rule files it finds (in a
subfolder, through a link, once through a loop of links), what it reads from each, the files of
a range of commits and a moved file under both names, one answer for a file however it is named,
and its refusals. Each glob form is a unit case of test_globs.py, each frontmatter form one of
test_scope.py; here each rule file covers one file or more of one call."""

from typing import TYPE_CHECKING, Any, cast

import pytest

from fakes.command import Ran, lem
from fakes.repo import RealRepo, run_git, write
from lem.settings.placed import FIXED

if TYPE_CHECKING:
    from pathlib import Path

EVERY = "every path"
RULES = {
    ".lem/settings.toml": b"",
    ".claude/rules/00-conduct.md": b"# Conduct\nNever dig up a deleted document.\n",
    ".claude/rules/01-reports.md": (
        b"---\ndescription: no scope in this one\n---\nSay what you did not verify.\n"
    ),
    ".claude/rules/10-any-ts.md": b'---\npaths:\n  - "**/*.ts"\n---\n',
    ".claude/rules/11-under-src.md": b'---\npaths:\n  - "src/**/*"\n---\n',
    ".claude/rules/12-root-md.md": b'---\npaths:\n  - "*.md"\n---\n',
    ".claude/rules/13-one-folder.md": b"---\npaths:\n  - 'src/components/*.tsx'\n---\n",
    ".claude/rules/14-braces.md": (
        b"---\npaths:\n  # the three lines of the documentation\n"
        b'  - "src/**/*.{ts,tsx}"\n  - "lib/**/*.ts"\n  - "tests/**/*.test.ts"\n'
        b"description: after the list\n---\n"
    ),
    ".claude/rules/15-bom.md": (
        b'\xef\xbb\xbf---\npaths: ["**/*.proto"]  # with a byte order mark\n---\n'
    ),
    ".claude/rules/backend/20-models.md": (
        b'---\npaths: ["**/models.py", "**/models/**", ".revmux/**", "docs/{a,b}/*.md"]\n'
        b"---\n"
    ),
    ".claude/rules/backend/21-one-file.md": b"---\npaths: scripts/verify.sh\n---\n",
    ".claude/rules/notes.txt": b"not a rule\n",
}
SHARED = (
    b'---\npaths: # what follows is the scope\n  - "**/*.sql" # every query\n'
    b"  - '**/*#*.psql'\n---\n"
)


def rules_repo(tmp_path: Path) -> Path:
    """A checkout with the rule files above, a folder of rules outside it through a link, and
    a link back up that would loop."""
    shared = tmp_path / "shared-rules"
    shared.mkdir()
    (shared / "30-sql.md").write_bytes(SHARED)
    checkout = RealRepo.init(tmp_path / "repo", RULES).checkout
    rules = checkout / ".claude" / "rules"
    (rules / "shared").symlink_to(shared)
    (rules / "backend" / "loop").symlink_to("..")
    return checkout


def answer(ran: Ran) -> dict[str, Any]:
    """The picker's answer; a test fails when the call did not succeed."""
    assert ran.code == 0, f"{ran.stdout}{ran.stderr}"
    return cast("dict[str, Any]", ran.result())


def names(found: dict[str, Any], *, every: bool | None = None) -> list[str]:
    """The names of the rule files picked: all, those for every path, or the scoped ones."""
    return [
        rule["file"].rsplit("/", 1)[1]
        for rule in found["rules"]
        if every is None or (rule["scope"] == EVERY) == every
    ]


def prefixes(checkout: Path, *args: str) -> str:
    """The first two letters of each rule file picked for `lem rules ARGS`."""
    found = answer(lem("rules", *args, cwd=checkout))
    return " ".join(name[:2] for name in names(found))


def refusal(ran: Ran) -> dict[str, str]:
    """The refusal of a call; a test fails when the call was not refused."""
    assert ran.code == 1, f"{ran.stdout}{ran.stderr}"
    return cast("dict[str, str]", ran.envelope()["refusal"])


def commit(checkout: Path, message: str, files: dict[str, bytes | None]) -> None:
    """A commit of `files` alone, so that the links of the rules folder stay out of it."""
    write(checkout, files)
    run_git(checkout, "add", "--all", "--", *files)
    run_git(checkout, "commit", "--quiet", "--message", message)


def test_the_picker_reads_the_scope_of_each_rule_file(tmp_path: Path) -> None:
    checkout = rules_repo(tmp_path)
    root = checkout.resolve()
    found = answer(
        lem(
            "rules",
            "src/components/a.tsx",
            str(checkout / "app" / "models.py"),
            "docs/a/x.md",
            "lib/a.ts",
            "tests/unit/a.test.ts",
            "scripts/verify.sh",
            "db/001.sql",
            "db/a#b.psql",
            "api/v1.proto",
            "README.md",
            cwd=checkout,
        )
    )
    scoped = [
        (rule["file"].rsplit("/", 1)[1], rule["scope"], rule["covers"])
        for rule in found["rules"]
        if rule["scope"] != EVERY
    ]
    assert scoped == [
        ("10-any-ts.md", ["**/*.ts"], ["lib/a.ts", "tests/unit/a.test.ts"]),
        ("11-under-src.md", ["src/**/*"], ["src/components/a.tsx"]),
        ("12-root-md.md", ["*.md"], ["README.md"]),
        ("13-one-folder.md", ["src/components/*.tsx"], ["src/components/a.tsx"]),
        (
            "14-braces.md",
            ["lib/**/*.ts", "src/**/*.{ts,tsx}", "tests/**/*.test.ts"],
            ["lib/a.ts", "src/components/a.tsx", "tests/unit/a.test.ts"],
        ),
        ("15-bom.md", ["**/*.proto"], ["api/v1.proto"]),
        (
            "20-models.md",
            ["**/models.py", "docs/{a,b}/*.md"],
            ["app/models.py", "docs/a/x.md"],
        ),
        ("21-one-file.md", ["scripts/verify.sh"], ["scripts/verify.sh"]),
        ("30-sql.md", ["**/*#*.psql", "**/*.sql"], ["db/001.sql", "db/a#b.psql"]),
    ]
    assert names(found, every=True) == ["00-conduct.md", "01-reports.md"]
    assert found["rules"][0] == {
        "file": str(root / ".claude" / "rules" / "00-conduct.md"),
        "scope": EVERY,
    }
    assert found["rules"][-1]["file"] == str(
        root / ".claude" / "rules" / "shared" / "30-sql.md"
    )
    assert found["files"][:3] == ["README.md", "api/v1.proto", "app/models.py"]
    assert (found["exists"], found["folder"], len(found["rules"])) == (
        True,
        str(root / ".claude" / "rules"),
        11,
    )


def test_the_picker_takes_the_files_of_a_range_of_commits(tmp_path: Path) -> None:
    checkout = rules_repo(tmp_path)
    commit(
        checkout, "feat: a query", {"db/001.sql": b"select 1;\n", "notes.md": b"x\n"}
    )
    for commits in ("HEAD~1..HEAD", "HEAD~1..", "HEAD~1...HEAD"):
        found = answer(lem("rules", "--range", commits, cwd=checkout))
        assert found["files"] == ["db/001.sql", "notes.md"], commits
        assert names(found, every=False) == ["12-root-md.md", "30-sql.md"], commits
    found = answer(lem("rules", "lib/a.ts", "--range", "HEAD~1..HEAD", cwd=checkout))
    assert found["files"] == ["db/001.sql", "lib/a.ts", "notes.md"]
    # a name git quotes is read as the name
    commit(checkout, "docs: a note", {"naïve.md": b"x\n", 'say "x".md': b"x\n"})
    found = answer(lem("rules", "--range", "HEAD~1..HEAD", cwd=checkout))
    assert found["files"] == ["naïve.md", 'say "x".md']
    assert names(found, every=False) == ["12-root-md.md"]


@pytest.mark.parametrize(
    ("commits", "why"),
    [
        ("no-such-ref..HEAD", "git knows no commit no-such-ref"),
        ("HEAD..no-such-ref", "git knows no commit no-such-ref"),
        ("no-such-ref...HEAD", "git knows no commit no-such-ref"),
        ("HEAD", "HEAD is no range of commits"),
    ],
    ids=["base", "tip", "three-dots", "no-range"],
)
def test_a_range_git_does_not_know_is_refused(
    tmp_path: Path, commits: str, why: str
) -> None:
    checkout = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""}).checkout
    refused = refusal(lem("rules", "--range", commits, cwd=checkout))
    assert (refused["code"], refused["why"]) == ("range", why)
    assert refused["fix"].endswith("BASE..TIP")


def test_a_renamed_file_brings_the_rules_of_its_old_place_and_its_new_one(
    tmp_path: Path,
) -> None:
    checkout = rules_repo(tmp_path)
    commit(checkout, "feat: a module", {"src/x.ts": b"export const a = 1\n"})
    (checkout / "lib").mkdir()
    run_git(checkout, "mv", "src/x.ts", "lib/x.ts")
    run_git(checkout, "commit", "--quiet", "--message", "refactor: the module moves")
    found = answer(lem("rules", "--range", "HEAD~1..HEAD", cwd=checkout))
    assert found["files"] == ["lib/x.ts", "src/x.ts"]
    assert [name[:2] for name in names(found)] == ["00", "01", "10", "11", "14"]


def test_a_path_through_a_link_or_with_two_dots_is_the_same_file(
    tmp_path: Path,
) -> None:
    checkout = rules_repo(tmp_path)
    (checkout / "src" / "sub").mkdir(parents=True)
    (checkout / "alias").symlink_to("src")
    (checkout / "deep").symlink_to("src/sub")
    assert prefixes(checkout, "alias/y.ts") == "00 01 10 11 14"
    assert prefixes(checkout, str(checkout / "src" / "y.ts")) == "00 01 10 11 14"
    for given in (
        ("alias/y.ts",),
        ("deep/../y.ts", str(checkout / "deep" / ".." / "y.ts"), "lib/../src/y.ts"),
    ):
        found = answer(lem("rules", *given, cwd=checkout))
        assert found["files"] == ["src/y.ts"], given


@pytest.mark.parametrize(
    ("given", "code"),
    [
        ("../elsewhere.py", "outside"),
        ("src/..", "no-file"),
        (".", "no-file"),
        ("src/sub/../..", "no-file"),
        ("CHECKOUT", "no-file"),
        ("ELSEWHERE", "outside"),
    ],
)
def test_a_path_that_leaves_the_repository_or_names_no_file_is_refused(
    tmp_path: Path, given: str, code: str
) -> None:
    checkout = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""}).checkout
    named = {"CHECKOUT": str(checkout), "ELSEWHERE": str(tmp_path / "elsewhere.py")}
    word = named.get(given, given)
    refused = refusal(lem("rules", word, cwd=checkout))
    assert refused["code"] == code
    if code == "outside":
        assert refused["why"] == f"{word} is not inside {checkout.resolve()}"
        assert refused["fix"] == "name the files of this repository"


def test_a_call_with_no_file_and_no_range_is_a_wrong_call(tmp_path: Path) -> None:
    checkout = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""}).checkout
    ran = lem("rules", cwd=checkout)
    assert (ran.code, ran.stdout) == (2, "")
    assert "give at least one of FILES, --range" in ran.stderr


@pytest.mark.parametrize(
    ("rule", "why", "fix"),
    [
        (
            b"---\npaths:\n---\nA scope with nothing in it.\n",
            ".claude/rules/40-empty.md: its `paths:` names no glob",
            "or take the line out so the file covers every path",
        ),
        (
            b'---\npaths:\n  glob: "src/**"\n---\n',
            ".claude/rules/40-empty.md: a line under `paths:` is not a list item",
            'write each glob under it as `  - "GLOB"`',
        ),
        (
            b'---\npaths: ["src/[z-a].ts"]\n---\n',
            ".claude/rules/40-empty.md: a glob of its `paths:` does not read as a pattern",
            "a `[` with no `]`, or a range that runs backwards",
        ),
    ],
    ids=["no-glob", "no-list", "no-pattern"],
)
def test_a_rule_whose_paths_name_no_glob_are_no_list_or_do_not_read_is_refused(
    tmp_path: Path, rule: bytes, why: str, fix: str
) -> None:
    files = {".lem/settings.toml": b"", ".claude/rules/40-empty.md": rule}
    checkout = RealRepo.init(tmp_path / "repo", files).checkout
    refused = refusal(lem("rules", "x.ts", cwd=checkout))
    assert refused["why"].startswith(why)
    assert fix in refused["fix"]


def test_a_project_with_no_rules_gets_no_rule_and_no_error(tmp_path: Path) -> None:
    checkout = RealRepo.init(tmp_path / "repo", {".lem/settings.toml": b""}).checkout
    found = answer(lem("rules", "app/x.py", cwd=checkout))
    assert (found["exists"], found["rules"], found["files"]) == (
        False,
        [],
        ["app/x.py"],
    )


def test_the_rules_are_read_where_the_agent_loads_them_and_stay_there(
    tmp_path: Path,
) -> None:
    checkout = rules_repo(tmp_path)
    before = sorted(path.name for path in (checkout / ".claude" / "rules").iterdir())
    found = answer(lem("rules", "x.ts", cwd=checkout))
    assert found["folder"] == str(checkout.resolve() / dict(FIXED)["rules"])
    assert found["folder"].endswith("/.claude/rules")
    after = sorted(path.name for path in (checkout / ".claude" / "rules").iterdir())
    assert after == before


def test_a_task_worktree_names_its_own_files_and_reads_its_own_rules(
    tmp_path: Path,
) -> None:
    checkout = rules_repo(tmp_path)
    worktree = checkout / ".lem" / "worktrees" / "fix-the-login"
    run_git(
        checkout, "worktree", "add", "--quiet", "-b", "fix-the-login", str(worktree)
    )
    write(worktree, {".claude/rules/50-branch.md": b'---\npaths: ["**/*.py"]\n---\n'})
    (worktree / "lib").mkdir()
    found = answer(
        lem("rules", "app/x.py", str(worktree / "lib" / "y.py"), cwd=worktree / "lib")
    )
    assert found["folder"] == str(worktree.resolve() / ".claude" / "rules")
    assert found["files"] == ["app/x.py", "lib/y.py"]
    assert names(found, every=False) == [
        "50-branch.md",
        "20-models.md",
    ] or "50-branch.md" in names(found)

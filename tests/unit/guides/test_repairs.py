"""The guide's promises that depend on what Lem does."""

import re
import subprocess

from unit.guides import built
from unit.guides.test_guides import DOCS, GUIDES, WORDS, text_of


def flat(text: str) -> str:
    """Ignore line breaks in prose."""
    return " ".join(text.split())


def test_the_approve_ruling_keeps_the_owners_words() -> None:
    rulings = text_of("rulings/rulings.md")
    bullet = re.search(
        r"- \*\*The board's button says Approve,.*?(?=\n- |\n\n)", rulings, re.DOTALL
    )
    assert bullet is not None
    assert flat(bullet[0]) == (
        "- **The board's button says Approve, the approval stands through a moved base and a conflict, "
        "and before an approved task merges on a moved base the checks run on the task rebased onto that base.** "
        "A task red on its rebase leaves the line and comes back after a builder's fix. "
        "Its session calls the owner only when the fix needs a criterion to change or a breaker applies. "
        "A task whose checks ran on the current base merges first. "
        "The board server records how many approved tasks wait at each merge. (2026-11-25)"
    )


def test_git_and_eslint_ignore_the_site_build() -> None:
    git = subprocess.run(
        ["git", "check-ignore", "--", "_site/index.html"],
        cwd=built.ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    lint = (built.ROOT / "eslint.config.mjs").read_text(encoding="utf-8")
    ignored = lint.split("globalIgnores([", 1)[1].split("])", 1)[0]
    assert (git.returncode, "'_site/'" in ignored) == (0, True)


def test_the_merge_guide_states_what_keeps_approval() -> None:
    guide = flat(text_of("merge.md"))
    assert 'while the reasons for "not green" stay the same' in guide
    assert "Approve the pull request again if your approval ends." in guide


def test_the_merge_rule_is_in_the_merge_guide_and_the_settings_and_one_line_elsewhere() -> (
    None
):
    chart = text_of("merge.md").split("```mermaid\n", 1)[1].split("```", 1)[0]
    assert "green, not careful" in chart
    assert "settings permit, verdict is merge" in chart
    merge = flat(text_of("merge.md"))
    assert (
        "Lem merges a **safe** change itself: it is green and not careful, the verdict is "
        'merge, and [`branch.land`](settings.md#branch) is `"agent"`' in merge
    )
    assert "[safe change](merge.md#the-merge-review)" in flat(text_of("settings.md"))
    home = text_of("index.md")
    assert "verdict is merge" not in home.split("```mermaid\n", 1)[1].split("```", 1)[0]
    assert "Lem merges a safe green change, and you merge the others." in flat(home)
    readme = flat((built.ROOT / "README.md").read_text(encoding="utf-8"))
    assert "Lem merges a safe green change. You merge the others." in readme
    for name in ("index.md", "flow.md", "phone.md", "board.md", "../README.md"):
        assert "branch.land" not in (DOCS / name).read_text(encoding="utf-8"), name


def test_the_merge_guide_limits_what_the_pull_request_says_about_a_conflict() -> None:
    conflict = flat(text_of("merge.md").split("## A conflict", 1)[1].split("##", 1)[0])
    assert "The pull request says when the merge review carries." in conflict
    assert "or why a merge agent reads it" not in conflict


def test_the_install_guide_reserves_existing_plugin_settings_for_the_owner() -> None:
    guide = flat(text_of("install.md"))
    assert (
        "`/lem init` commits `.claude/settings.json` only if git does not track it"
        in guide
    )
    assert (
        "`extraKnownMarketplaces` for `lem` and `enabledPlugins` for `lem@lem`" in guide
    )
    assert "Commit any other `.claude/settings.json` yourself." in guide


def test_the_ticket_guide_keeps_the_state_of_an_issue_after_a_drop() -> None:
    issues = text_of("tickets.md").split("\n## GitHub Issues\n", 1)[1]
    writes = issues.split("Lem writes to the issue at these steps:", 1)[1]
    stopped = flat(writes.split("\n### ", 1)[0].split("4. ", 1)[1])
    assert stopped.startswith("The task stops with no merge")
    assert "An open issue stays open and a closed issue stays closed." in stopped


def test_the_merge_guide_tells_the_owner_how_to_order_several_merges() -> None:
    guide = flat(text_of("merge.md"))
    assert "Lem merges them in the order you give." in guide
    assert "If you give no order, Lem starts with the oldest pull request." in guide


def test_a_note_that_changes_no_criterion_leads_to_the_same_criteria() -> None:
    guide = flat(text_of("when-lem-needs-you.md"))
    assert "When your note changes no criterion" in guide
    assert "asks for your yes to the same criteria" in guide


def test_the_checks_keep_the_baseline_journey_and_timing_rules() -> None:
    checks = (
        (built.ROOT / "AGENTS.md").read_text(encoding="utf-8").split("## Checks", 1)[1]
    )
    checks = flat(checks.split("\n## ", 1)[0])
    assert "Use the counts of the last full run as the baseline." in checks
    assert (
        "Run one journey for the path. Test its other inputs at a lower level."
        in checks
    )
    assert (
        "Never make a timing assertion depend on a step that finishes in less than one second."
        in checks
    )


def test_agents_md_explains_how_the_session_and_pair_load_the_plugin() -> None:
    agents = flat((built.ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    assert (
        "When the project has no enabled install of `lem@lem`, `lem session open` adds "
        "`--plugin-dir` with the app's own data folder." in agents
    )
    assert (
        "reads the folder for the plan talk's pair from `lem session plugin-dir`"
        in agents
    )


def test_agents_md_explains_the_decided_lines_in_the_history() -> None:
    agents = flat((built.ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    assert (
        "The `decided` lines of `docs/rulings/history.md` are choices of the maintaining "
        "session that a test or one place holds." in agents
    )


def test_the_backlog_lists_guides_over_the_aim_with_their_source_word_counts() -> None:
    counts = {name: len(text_of(name).split()) for name in GUIDES}
    long = {name: count for name, count in counts.items() if count >= WORDS}
    path = DOCS / "backlog/five-guides-run-past-the-800-word-aim.md"
    item = path.read_text(encoding="utf-8") if path.is_file() else ""
    entries = re.findall(r"^- `([^`]+\.md)` has (\d+) words\.$", item, re.MULTILINE)
    assert {name: int(count) for name, count in entries} == long


def test_the_ledger_names_the_scope_of_the_skill_voice_proof() -> None:
    ledger = built.ROOT / "tests/ledger/fates/guides.tsv"
    row = next(
        line
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.startswith("ruling:the-skill-files-keep-their-own-voice-")
    )
    assert "AGENTS.md states the rule" in row.split("\t")[3]


def test_the_site_reader_has_no_unused_html_unescape_wrapper() -> None:
    assert not hasattr(built, "unescaped")

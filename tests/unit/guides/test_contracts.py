"""The guide text at the points where the owner must act."""

from unit.guides.test_guides import ROOT, text_of


def guide(name: str) -> str:
    return " ".join(text_of(name).split())


def test_update_gives_task_recovery_and_no_steps_for_lem_03_or_https() -> None:
    """The owner's read of 2026-11-27: nobody but his own copies runs Lem 0.3, and the
    repository is open, so an update needs no key. `lem doctor` still names a folder of 0.3."""
    update = guide("update.md")
    assert "Lem 0.3" not in update
    assert "HTTPS" not in update
    recovery = update[update.index("## A task of an older release") :]
    assert "use the current record format" in recovery
    assert recovery.index("/lem drop") < recovery.index("/lem resume")


def test_update_requires_a_new_session_with_the_matching_plugin() -> None:
    update = guide("update.md")
    assert "keeps its old plugin loaded" in update
    assert "refuses task commands" in update
    assert "Start a new session with the matching plugin" in update


def test_standard_track_waits_for_the_owner_only_when_needed() -> None:
    flow = guide("flow.md")
    standard = flow.split("## The standard track", 1)[1].split(" ##", 1)[0]
    assert "your complete request" in standard
    assert "if the personas agree" in standard
    assert "If you are present" in standard
    assert (
        "an interview, a disputed criterion or a request from another person"
        in standard
    )
    chart = text_of("index.md").split("```mermaid", 1)[1].split("```", 1)[0]
    assert "Interview if needed, then criteria" in chart
    assert "approval if needed" in chart
    assert "```mermaid" not in text_of("flow.md"), (
        "the Overview's chart is the one chart"
    )


def test_board_approval_can_carry_and_the_board_server_merges_only_a_safe_change() -> (
    None
):
    board = guide("board.md")
    assert "**Approve** authorizes" in board
    assert "approval can carry to a new commit" in board
    assert "(merge.md#merge-it)" in board
    assert "merges each [safe change](merge.md#the-merge-review)" in board


def test_a_moved_base_is_read_and_an_approved_task_is_rebased_and_checked_again() -> (
    None
):
    merge = guide("merge.md")
    assert (
        "If the base moved, Lem reads the change, and rebases when necessary." in merge
    )
    assert (
        "Lem always rebases an approved task on a moved base, and runs the checks again "
        "before the merge." in merge
    )
    assert "`Base:" not in merge, "the words between agents stay out of the guide"


def test_squash_body_names_decisions_and_the_pull_request_lists_fixes() -> None:
    merge = guide("merge.md")
    assert "the body of Lem's commit lists the task's decisions" in merge
    assert "the note about a moved base" in merge
    assert "`Lem task: <task>`" in merge
    assert "[Fixed on the way](pull-request.md#what-lem-saw-outside-the-task)" in merge


def test_green_accounts_for_the_owner_and_the_merge_review() -> None:
    pull = guide("pull-request.md")
    assert "You can clear this reason if you approve the revised criteria" in pull
    assert "a change you make through a breaker" in pull
    assert "the lead made a choice that the ladder could not settle" in pull
    for text in (pull, guide("index.md")):
        assert (
            "A careful change or a call from the merge agent still needs your read"
            in text
        )


def test_board_waits_go_most_urgent_first_and_in_a_group_oldest_first() -> None:
    guide_text = guide("when-lem-needs-you.md")
    assert (
        "The most urgent thing comes first: breakers and stopped sessions, then questions "
        "and other waits, then plans to read, then merges. In a group, the oldest wait "
        "comes first." in guide_text
    )


def test_home_lists_the_helpers_and_requires_consent_for_jobs() -> None:
    home = guide("index.md")
    for example in (
        "/lem root-cause the import stops at row 5000",
        "/lem ask-expert",
        "/lem panel docs/backlog/export-drops-custom-columns.md",
    ):
        assert example in home
    assert "Lem needs your yes at setup" in home
    assert "`/lem retro`" in home and "`/lem night`" in home


def test_maintainer_rules_cover_command_output_plan_changes_and_time_limits() -> None:
    agents = " ".join((ROOT / "AGENTS.md").read_text(encoding="utf-8").split())
    assert "`lem help` prints text" in agents
    assert "`lem version` prints JSON with no envelope" in agents
    assert "exit 2" in agents
    assert "where later decisions changed it" in agents
    assert "A level that reaches its 30-minute time limit fails" in agents

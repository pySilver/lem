"""The guide text at the points where the owner must act."""

from unit.guides.test_guides import ROOT, text_of


def guide(name: str) -> str:
    return " ".join(text_of(name).split())


def test_update_from_lem_03_starts_over_before_task_recovery() -> None:
    update = guide("update.md")
    cutover = update.index("## From Lem 0.3")
    recovery = update.index("## A task of an older release")
    old = update[cutover:recovery]
    assert "start over" in old
    assert "folders of Lem 0.3" in old
    assert old.index("Stop the Lem 0.3 board server") < old.index("`lem doctor`")
    assert old.index("`lem doctor`") < old.index("Move")
    assert "/lem drop" not in old and "/lem resume" not in old
    assert "use the current record format" in update[recovery:]


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
    for name in ("flow.md", "index.md"):
        chart = text_of(name).split("```mermaid", 1)[1].split("```", 1)[0]
        assert "Interview if needed, then criteria" in chart
        assert "approval if needed" in chart


def test_board_approval_can_carry_and_the_phone_respects_merge_authority() -> None:
    board = guide("board.md")
    assert "**Approve** authorizes" in board
    assert "approval can carry to a new commit" in board
    assert "(merge.md#merge-it)" in board
    phone = guide("phone.md")
    assert '`branch.land = "owner"`' in phone
    assert "you merge even if the verdict is merge" in phone
    assert "(merge.md#the-merge-review)" in phone


def test_moved_base_has_two_outcomes_for_an_automatic_merge() -> None:
    merge = guide("merge.md")
    assert (
        "a fresh merge agent reads any change to the base tree since the checks"
        in merge
    )
    assert "`Base: safe.`" in merge and "without a new run" in merge
    assert "`Base: another round.`" in merge and "runs the checks again" in merge
    assert "the pull request gives both bases and the reason" in merge


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


def test_board_waits_in_the_same_group_go_oldest_first() -> None:
    guide_text = guide("when-lem-needs-you.md")
    groups = guide_text.split("in this order:", 1)[1].split("A task is on the list", 1)[
        0
    ]
    same = groups.split("2. ", 1)[1].split("3. ", 1)[0]
    for reason in ("criteria", "your action or a fact", "cards", "dropped", "blocked"):
        assert reason in same
    assert "the oldest wait comes first" in same


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

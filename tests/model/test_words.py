"""The words the landing reads and writes, over drawn texts (`model/landing/propose_jev.py`,
`merge_lines.py`, `item_names.py`, `jev_bar.py`, `propose_careful.py`, `filing_flags.py`,
`propose_facts.py`): Jev stops a proposal only for a finding it reads over the bar, and names
each; a line goes into the pull request's text once; an item's names never repeat; the bar has a
condition only in a rule 6 that says one; and the careful line of a settings edit says what the
edit did."""

from hypothesis import given
from hypothesis import strategies as st
from msgspec.structs import replace

from lem.model.landing import (
    careful,
    filing_flags,
    item_names,
    jev_bar,
    merge_lines,
    propose_careful,
    propose_jev,
    propose_notes,
)
from lem.model.landing.items import BacklogItem, Defect
from lem.model.landing.propose_facts import Facts, Settings, small
from lem.records.criteria import Criteria
from lem.records.landing.review import JevRead
from model.landings import LANDING, shas
from unit.landing.worlds import MOMENT, task

SCORES = st.none() | st.floats(min_value=0, max_value=1)
KEYS = st.sampled_from(("a.py drops a line", "docs/backlog/x.md", "`b.py`: a nit"))
WORDS = st.text(alphabet="abc `:-_./\n", max_size=30)
TEAM = st.sampled_from(
    (None, "", "[branch]\nland = 'agent'\n", "[branch]\nland='agent'\n", "[checks]\n")
)


@LANDING
@given(
    st.dictionaries(KEYS, SCORES, max_size=3), st.tuples(st.booleans(), st.booleans())
)
def test_jev_stops_a_proposal_only_for_a_finding_it_reads_over_the_bar_and_names_each(
    scores: dict[str, float | None], flags: tuple[bool, bool]
) -> None:
    refused, reason = flags
    blocked = {}
    for label, score in scores.items():
        defect = Defect(where="", title=label, what=label)
        finding = propose_jev.Asked(label=label, defect=defect, reason=reason)
        read = JevRead(key=finding.key, at=MOMENT, score=score, refused=refused)
        over = propose_jev.blocked(finding, read)
        assert (over is not None) == (
            score is not None and score >= 0.7 and (not refused or not reason)
        )
        if over is not None:
            blocked[label] = over
    if blocked:
        found = propose_jev.refused("fix-the-login", blocked)
        assert found.code == "jev-over"
        assert all(f'"{label}" (Jev: ' in found.why for label in blocked)
        assert "fix-the-login" in found.fix


@LANDING
@given(st.lists(WORDS, min_size=1, max_size=3))
def test_a_notes_entry_is_asked_of_jev_only_when_it_calls_itself_under_the_bar(
    entry: list[str],
) -> None:
    asked = propose_jev.line_asked(tuple(entry))
    text = "\n".join(entry)
    assert (asked is None) == (propose_jev.UNDER.search(text) is None)
    if asked is not None:
        assert asked.label == entry[0].strip()
        defect = asked.defect
        assert defect.what == defect.title
        assert defect.where == propose_jev.where_of(defect.title)
        assert not defect.where or f"`{defect.where}`" in defect.title


@LANDING
@given(st.sampled_from(("none", "- a.py drops a line; under: a reader meets it")))
def test_jev_reads_each_item_called_not_worth_it_and_each_notes_line_called_under(
    line: str,
) -> None:
    record = task(phase="preparing")
    notes = propose_notes.parsed(f"{line}\n")
    assert isinstance(notes, propose_notes.Notes)
    items = (
        BacklogItem(path="docs/backlog/x.md", title="x breaks", worth="no"),
        BacklogItem(path="docs/backlog/y.md", title="y breaks", worth="no"),
    )
    asked = propose_jev.asked(record, notes, Facts(under=items))
    assert [one.label for one in asked[:2]] == [
        "docs/backlog/x.md",
        "docs/backlog/y.md",
    ]
    assert [one.defect.title for one in asked[:2]] == ["x breaks", "y breaks"]
    lines = asked[2:]
    assert len(lines) == (0 if line == "none" else 1)
    if lines:
        assert lines[0].defect.title == "a.py drops a line"


@LANDING
@given(
    st.text(max_size=40), st.sampled_from(("The checks ran on main.", "Lem task: x"))
)
def test_a_line_goes_into_the_pull_request_s_text_once(body: str, line: str) -> None:
    noted = merge_lines.noted_body(body, line)
    if line in body:
        assert noted is None
        return
    assert noted is not None
    assert noted.endswith(f"{line}\n")
    assert noted.startswith(body.rstrip("\n"))
    assert merge_lines.noted_body(noted, line) is None


@LANDING
@given(
    branch=st.sampled_from(("docs/fix-the-login",)),
    tip=shas(),
    after=st.booleans(),
    inside=st.booleans(),
)
def test_why_a_landed_branch_stays_names_one_cause(
    branch: str, tip: str, *, after: bool, inside: bool
) -> None:
    why = merge_lines.unmerged_why("main", (branch, tip), after=after, inside=inside)
    causes = (
        "commits after the head the forge merged",
        '"Update branch"',
        "the forge did not merge its tip",
    )
    named = [cause for cause in causes if cause in why]
    assert len(named) == 1
    assert named[0] == causes[0 if after else 1 if inside else 2]


@LANDING
@given(
    st.text(alphabet="ab -", min_size=1, max_size=20),
    st.sampled_from(("", "src/json.py:parse", "a.py")),
)
def test_an_item_s_names_never_repeat_and_start_with_its_title(
    title: str, where: str
) -> None:
    defect = Defect(where=where, title=title, what="it")
    names = item_names.names_for(defect)
    first = [next(names) for _ in range(4)]
    assert len(set(first)) == len(first)
    assert first[0] == f"{item_names.slug_of(title)}.md"


@LANDING
@given(
    st.sampled_from(
        (
            "",
            "5. one\n6. two\n",
            "6. It is **filed only for a defect over the bar: it costs a user**. More.\n7. x",
        )
    )
)
def test_the_bar_has_a_condition_only_in_a_rule_6_that_says_one(text: str) -> None:
    found = jev_bar.condition(text)
    if "6." not in text or "filed only" not in text:
        assert found is None
    else:
        assert found == "it costs a user"


@LANDING
@given(TEAM, TEAM, st.tuples(st.booleans(), st.booleans()))
def test_the_careful_line_of_a_settings_edit_says_what_the_edit_did(
    before: str | None, after: str | None, local: tuple[bool, bool]
) -> None:
    settings = Settings(before=before, after=after, local=local)
    team, machine = propose_careful.edits(
        Facts(
            changed=(careful.SETTINGS_FILE, careful.LOCAL_SETTINGS_FILE),
            settings=settings,
        )
    )
    if after is None:
        assert "removes" in team
    elif careful.tables_edited(before or "", after) == []:
        assert "the text of .lem/settings.toml, and no value in it" in team
    else:
        assert "] of .lem/settings.toml" in team
    how = {(False, True): "adds", (True, False): "removes"}.get(local, "changes")
    assert f"the change {how} .lem/settings.local.toml" in machine


@LANDING
@given(
    st.sets(st.sampled_from(("r1.1", "r1.2", "r2.1"))),
    st.sets(st.sampled_from(("r1.1", "r1.2"))),
)
def test_same_and_new_name_only_a_defect_that_waits_for_an_item(
    named: set[str], free: set[str]
) -> None:
    found = filing_flags.stray_refused(named, free)
    assert (found is None) == (named <= free)
    if found is not None:
        ending = "the ones here are" if free else "none waits here"
        assert ending in found.why


@LANDING
@given(
    st.sampled_from((None, "small", "full")),
    st.sampled_from((None, "small", "full")),
)
def test_a_task_is_on_the_fast_track_by_its_criteria_s_size_else_its_shape(
    size: str | None, track: str | None
) -> None:
    record = task()
    shape = record.task.shape
    assert shape is not None
    criteria = replace(record.task.criteria, size=size)
    made = replace(
        record.task,
        criteria=criteria if size else Criteria(),
        shape=replace(shape, track=track) if track else None,
    )
    assert small(replace(record, task=made)) == ((size or track) == "small")

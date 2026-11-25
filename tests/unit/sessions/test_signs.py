"""The rules of a Claude Code transcript's signs (`claude_turns`, `claude_tail`): whether the main
thread's newest turn runs, its newest sign, and the read of a file from its end, over records of
the forms the probes of 2026-11-23 read on the owner's Mac (`signs.py` on `main`)."""

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lem.adapters import claude_tail, claude_transcript, claude_turns

if TYPE_CHECKING:
    from pathlib import Path


def newest_first(*records: object) -> list[claude_transcript.Entry]:
    """`records`, oldest first as a transcript holds them, as the signs read them: from the
    end."""
    lines = [json.dumps(each).encode() for each in reversed(records)]
    return list(claude_transcript.entries(lines))


def turn(*records: object) -> str | None:
    return claude_turns.turn_of(newest_first(*records))


def user(content: object, **flags: object) -> dict[str, object]:
    return {
        "type": "user",
        "timestamp": "2026-11-23T11:42:52.100Z",
        "message": {"role": "user", "content": content},
        **flags,
    }


def assistant(
    stop_reason: str | None, *content: dict[str, object], **flags: object
) -> dict[str, object]:
    return {
        "type": "assistant",
        "timestamp": "2026-11-23T11:42:55.300Z",
        "message": {
            "role": "assistant",
            "stop_reason": stop_reason,
            "content": list(content) or [{"type": "text", "text": "x"}],
        },
        **flags,
    }


def tool(name: str) -> dict[str, object]:
    return {"type": "tool_use", "id": "toolu_01", "name": name, "input": {}}


PROMPT = user("Discuss in chat: criterion 4 says the wrong hour")
RESULT = user([{"type": "tool_result", "tool_use_id": "toolu_01", "content": "ok"}])
ENDED = assistant("end_turn")
CAVEAT = user(
    "<local-command-caveat>The command below was run directly in Claude Code, not sent to "
    "you.</local-command-caveat>",
    isMeta=True,
)
RELOAD = user(
    "<command-name>/reload-plugins</command-name>\n"
    "            <command-message>reload-plugins</command-message>\n"
    "            <command-args></command-args>"
)
LOCAL_SYSTEM = {
    "type": "system",
    "subtype": "local_command",
    "timestamp": "2026-11-23T11:44:00Z",
    "content": "<local-command-stdout>(no content)</local-command-stdout>",
}
STDOUT = user("<local-command-stdout>Set model to `Opus 5.5`</local-command-stdout>")
LEM = user(
    "<command-message>lem:lem</command-message>\n"
    "<command-name>/lem:lem</command-name>\n<command-args>status</command-args>"
)
SKILL = user(
    [
        {
            "type": "text",
            "text": "Base directory for this skill: /Users/someone/.claude/plugins/lem",
        }
    ],
    isMeta=True,
)
SUMMARY = user(
    "This session is being continued from a previous conversation that ran out of context.",
    isCompactSummary=True,
)
ENDED_AT = datetime(2026, 11, 23, 11, 42, 55, tzinfo=UTC)


def test_a_prompt_and_a_tools_result_run() -> None:
    assert turn(ENDED, PROMPT) == "runs"
    assert turn(PROMPT, assistant("tool_use", tool("Bash")), RESULT) == "runs"
    assert turn(PROMPT, assistant("tool_use", tool("Bash"))) == "runs"


def test_end_turn_after_a_tools_result_ended() -> None:
    assert turn(PROMPT, assistant("tool_use", tool("Bash")), RESULT, ENDED) == "ended"
    for reason in ("stop_sequence", "refusal", "max_tokens"):
        assert turn(PROMPT, assistant(reason)) == "ended", reason


def test_an_interrupt_ended() -> None:
    running = assistant("tool_use", tool("Bash"))
    stopped = user([{"type": "text", "text": "[Request interrupted by user]"}])
    assert turn(PROMPT, running, stopped) == "ended"
    for_tool = [{"type": "text", "text": "[Request interrupted by user for tool use]"}]
    assert turn(PROMPT, running, RESULT, user(for_tool)) == "ended"
    assert turn(PROMPT, user("[Request interrupted by user]")) == "ended"


def test_a_local_command_after_end_turn_runs_no_turn() -> None:
    assert turn(PROMPT, ENDED, CAVEAT, RELOAD, LOCAL_SYSTEM, STDOUT) == "ended"
    shell = user("<bash-stdout>a</bash-stdout><bash-stderr></bash-stderr>")
    assert turn(PROMPT, ENDED, user("<bash-input>ls</bash-input>"), shell) == "ended"


def test_a_lem_command_with_its_skill_text_runs() -> None:
    assert turn(ENDED, CAVEAT, LEM, SKILL) == "runs"
    # The command alone, before its skill text is written, is no turn.
    assert turn(ENDED, LEM) == "ended"


def test_a_compactions_summary_after_end_turn_runs_no_turn() -> None:
    assert turn(PROMPT, ENDED, SUMMARY) == "ended"


def test_the_question_widget_asks_the_owner_and_ended() -> None:
    question: dict[str, object] = {"type": "text", "text": "One question:"}
    asks = assistant("tool_use", question, tool("AskUserQuestion"))
    assert turn(PROMPT, asks) == "ended"
    # His answer is the tool's result: the turn runs again.
    assert (
        turn(PROMPT, assistant("tool_use", tool("AskUserQuestion")), RESULT) == "runs"
    )


def test_a_sidechain_record_is_skipped() -> None:
    looked = user("Look at the code", isSidechain=True)
    reading = assistant("tool_use", tool("Read"), isSidechain=True)
    assert turn(PROMPT, ENDED, looked, reading) == "ended"


def test_a_record_with_no_stop_reason_is_skipped() -> None:
    assert turn(PROMPT, ENDED, assistant(None)) == "ended"
    empty = {
        "type": "assistant",
        "timestamp": "2026-11-23T11:43:00Z",
        "message": {"content": []},
    }
    assert turn(ENDED, PROMPT, empty) == "runs"


def test_no_decisive_record_is_none() -> None:
    assert turn() is None
    others = (
        {"type": "permission-mode"},
        CAVEAT,
        RELOAD,
        LOCAL_SYSTEM,
        SUMMARY,
        assistant(None),
        {"type": "queue-operation", "operation": "enqueue"},
        {"type": "attachment"},
    )
    assert turn(*others) is None
    lines = (b"half a line", b"", b"[]")
    assert claude_turns.turn_of(claude_transcript.entries(lines)) is None


def test_the_turn_reads_its_records_newest_first() -> None:
    assert turn(PROMPT, ENDED) == "ended"
    assert turn(ENDED, PROMPT) == "runs"


def test_a_record_whose_time_does_not_read_still_decides_the_turn() -> None:
    bad = {**assistant("end_turn"), "timestamp": "2026-02-31T10:00:00Z"}
    records = newest_first(PROMPT, assistant("tool_use", tool("Bash")), bad)
    assert claude_turns.turn_of(records) == "ended"
    assert claude_turns.newest_sign(records) == ENDED_AT


# The records after a turn that run none, as Claude Code 2.1.330 writes them (2026-11-22).
AFTER = (
    {"type": "user", "timestamp": "2026-11-22T10:15:37.756Z"},
    {
        "type": "assistant",
        "timestamp": "2026-11-22T10:15:42.728Z",
        "message": {"content": [{"type": "text", "text": "x" * 300}]},
    },
    {"type": "system", "timestamp": "2026-11-22T10:15:43.321Z"},
    {"type": "attachment", "timestamp": "2026-11-22T10:45:48.831Z"},
    {"type": "continued-in", "timestamp": "2026-11-22T10:45:49.327Z"},
    # The owner's wake reached the parked pane: a record, and no turn (f0410fb9 of #37).
    {
        "type": "queue-operation",
        "operation": "enqueue",
        "timestamp": "2026-11-22T15:53:31.059Z",
    },
    {"type": "cost-state"},
)
REPLIED_AT = datetime(2026, 11, 22, 10, 15, 42, tzinfo=UTC)


def test_a_queue_operation_after_the_newest_turn_moves_no_sign() -> None:
    assert claude_turns.newest_sign(newest_first(*AFTER)) == REPLIED_AT
    assert claude_turns.newest_sign(newest_first(*AFTER[2:])) is None


def test_a_local_commands_output_after_the_newest_turn_moves_no_sign() -> None:
    # After an unread stop, the owner asks for the cost in the pane whose turn had ended: the
    # local command's output runs no turn, so the sign stays at the end of the turn.
    later = "2026-11-23T12:30:00Z"
    cost = user("<command-name>/cost</command-name>")
    stdout = user("<local-command-stdout>Total cost: $1.20</local-command-stdout>")
    records = newest_first(
        PROMPT,
        ENDED,
        {**CAVEAT, "timestamp": later},
        {**cost, "timestamp": later},
        {**stdout, "timestamp": later},
        {**SUMMARY, "timestamp": later},
    )
    assert claude_turns.turn_of(records) == "ended"
    assert claude_turns.newest_sign(records) == ENDED_AT


def test_the_file_is_read_from_its_end_in_blocks(tmp_path: Path) -> None:
    path = tmp_path / "t.jsonl"
    lines = "".join(f"{json.dumps(each)}\n" for each in AFTER)
    path.write_text(f"half a line\n{lines}")
    expected = list(reversed(path.read_bytes().split(b"\n")[:-1]))
    for block in (7, 64, 100000):
        read = [line for line in claude_tail.tail_lines(path, block) if line]
        assert read == expected, block
    assert claude_tail.file_sign(path) == REPLIED_AT
    assert claude_tail.file_sign(tmp_path / "gone.jsonl") is None
    assert claude_tail.file_turn(tmp_path / "gone.jsonl") is None

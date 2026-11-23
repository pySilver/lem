"""lem_tokens.py: the tokens of a task's Claude Code sessions, over small transcripts in the form Claude
Code writes them (one record a line; a reply's blocks share one `message.id` and its `usage`).

    python3 -B -m unittest discover -s tests/unit
"""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "skills" / "lem" / "scripts")
)
lem_tokens = importlib.import_module("lem_tokens")

SLUG = "gift-note"


def reply(
    message: str,
    given: int,
    said: int,
    read: int = 0,
    wrote: int = 0,
    side: bool = False,
) -> dict:
    return {
        "type": "assistant",
        "isSidechain": side,
        "message": {
            "id": message,
            "role": "assistant",
            "content": [{"type": "text", "text": "x"}],
            "usage": {
                "input_tokens": given,
                "output_tokens": said,
                "cache_read_input_tokens": read,
                "cache_creation_input_tokens": wrote,
                "output_tokens_details": {"thinking_tokens": 1},
                "service_tier": "standard",
            },
        },
    }


def prompt(text: str, kind: str | None = None) -> dict:
    """A transcript's user record, in the form 6fe214ec has (2026-11-22): a fork's records carry `sessionKind: bg`."""
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        **({"sessionKind": kind} if kind else {}),
    }


def launch(slug: str) -> str:
    """The first prompt `lem session open` gives the session of task SLUG (session.py `launch_line`)."""
    return f"Read /Users/dev/shop/.lem/state/tasks/{slug}/session.md and follow it."


# the records Claude Code writes before a session's first prompt, and a meta prompt, as 6fe214ec has them
HEAD = (
    {"type": "ai-title"},
    {"type": "permission-mode"},
    {"type": "queue-operation"},
    {
        "type": "user",
        "isMeta": True,
        "message": {
            "role": "user",
            "content": "<local-command-caveat>x</local-command-caveat>",
        },
    },
)


def write(file: Path, *records: object) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        "".join(
            (record if isinstance(record, str) else json.dumps(record)) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


class Tokens(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.state = root / "state"
        self.state.mkdir()
        self.projects = root / "projects" / "-shop"

    def log(self, *transcripts: tuple[str, str]) -> None:
        lines = [
            {
                "ts": "2026-11-21T10:00:00Z",
                "event": "session.open",
                "task": SLUG,
                "session": "S-1",
            }
        ]
        lines += [
            {
                "ts": "2026-11-21T10:00:01Z",
                "event": "session.transcript",
                "task": task,
                "claude": Path(path).stem,
                "transcript": path,
                "source": "startup",
            }
            for task, path in transcripts
        ]
        write(self.state / "events.jsonl", *lines)

    def test_a_task_with_no_transcript_on_record_has_no_number(self):
        self.log()
        self.assertIsNone(lem_tokens.task_tokens(self.state, SLUG))

    def test_each_reply_counts_once_with_its_subagents_and_another_tasks_session_counts_for_none(
        self,
    ):
        first, second, other = (
            self.projects / f"{name}.jsonl" for name in ("aaa", "bbb", "ccc")
        )
        # one reply written as two records (two blocks), a user record, a line that does not read
        write(
            first,
            {"type": "user", "message": {"content": "go"}},
            reply("m1", 3, 100, 1000, 50),
            reply("m1", 3, 100, 1000, 50),
            reply("m2", 2, 10),
            "{half",
        )
        write(
            self.projects / "aaa" / "subagents" / "agent-a1.jsonl",
            reply("s1", 5, 20, 7, 9, side=True),
            reply("s1", 5, 20, 7, 9, side=True),
        )
        (self.projects / "aaa" / "subagents" / "agent-a1.meta.json").write_text(
            '{"agentType": "lem:lem-builder"}'
        )
        write(second, reply("m3", 1, 1))
        write(other, reply("m9", 1000, 1000))
        self.log(
            (SLUG, str(first)),
            (SLUG, str(second)),
            (SLUG, str(first)),
            ("another-task", str(other)),
        )
        found = lem_tokens.task_tokens(self.state, SLUG)
        self.assertEqual(
            {
                key: found[key]
                for key in (
                    "input",
                    "output",
                    "cache_read",
                    "cache_write",
                    "sessions",
                    "subagents",
                    "missing",
                    "unread",
                )
            },
            {
                "input": 11,
                "output": 131,
                "cache_read": 1007,
                "cache_write": 59,
                "sessions": 2,
                "subagents": 1,
                "missing": 0,
                "unread": 1,
            },
        )
        self.assertIn("(2) and their subagents (1)", found["covers"])
        self.assertIn(
            "a Codex reviewer, an expert of another provider and a session on another machine are not in it",
            found["covers"],
        )

    def test_a_transcript_that_is_gone_is_counted_and_said(self):
        kept = self.projects / "aaa.jsonl"
        write(kept, reply("m1", 1, 2))
        self.log((SLUG, str(kept)), (SLUG, str(self.projects / "gone.jsonl")))
        found = lem_tokens.task_tokens(self.state, SLUG)
        self.assertEqual(
            (found["output"], found["sessions"], found["missing"]), (2, 1, 1)
        )
        self.assertIn("1 transcript the log names is gone", found["covers"])

    def test_a_log_whose_words_hold_a_line_separator_still_names_the_transcript(self):
        kept = self.projects / "aaa.jsonl"
        write(kept, reply("m1", 1, 2))
        self.log((SLUG, str(kept)))
        # a folder's name may hold the characters str.splitlines breaks at, and the log keeps them as they are
        named = str(
            self.projects / "a\N{LINE SEPARATOR}b\N{PARAGRAPH SEPARATOR}c\x85d.jsonl"
        )
        with (self.state / "events.jsonl").open("a", encoding="utf-8") as log:
            log.write(
                json.dumps(
                    {
                        "ts": "2026-11-21T10:00:02Z",
                        "event": "session.transcript",
                        "task": SLUG,
                        "claude": "bbb",
                        "transcript": named,
                        "source": "resume",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, SLUG), [str(kept), named]
        )


class FirstPrompt(unittest.TestCase):
    """Which task a transcript counts for: the task its first prompt names, else the task its record names
    (criteria 1 and 2 of the task a-forked-transcript-of-claude-code-s-daemon-is-logged-on-the-task-of-another-pane)."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.state = root / "state"
        self.state.mkdir()
        self.projects = root / "projects" / "-shop"

    def log(self, *records: dict) -> None:
        write(
            self.state / "events.jsonl",
            {
                "ts": "2026-11-22T01:33:00Z",
                "event": "session.open",
                "task": "board-card-search",
                "session": "S-1",
            },
            *records,
        )

    @staticmethod
    def logged(
        task: str, path: Path, source: str = "startup", at: str = "2026-11-22T01:33:27Z"
    ) -> dict:
        return {
            "ts": at,
            "event": "session.transcript",
            "task": task,
            "claude": path.stem,
            "transcript": str(path),
            "source": source,
        }

    def test_a_fork_logged_under_another_task_counts_for_the_task_its_first_prompt_names_once(
        self,
    ):
        search, merge, fork = (
            self.projects / f"{name}.jsonl" for name in ("search", "merge", "6fe214ec")
        )
        write(search, *HEAD, prompt(launch("board-card-search")), reply("a1", 1, 10))
        write(
            merge, *HEAD, prompt(launch("merge-leaves-board-lock")), reply("b1", 1, 200)
        )
        # the fork copies its parent's first prompt, and the hook in the host of board-card-search's pane logged it there
        write(
            fork,
            *HEAD,
            prompt(launch("merge-leaves-board-lock"), "bg"),
            reply("f1", 1, 3000),
            reply("f1", 1, 3000),
        )
        self.log(
            self.logged("board-card-search", search),
            self.logged("merge-leaves-board-lock", merge),
            self.logged("board-card-search", fork, "fork", "2026-11-22T10:45:56Z"),
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, "board-card-search"), [str(search)]
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, "merge-leaves-board-lock"),
            [str(merge), str(fork)],
        )
        search_count = lem_tokens.task_tokens(self.state, "board-card-search")
        merge_count = lem_tokens.task_tokens(self.state, "merge-leaves-board-lock")
        self.assertEqual((search_count["output"], search_count["sessions"]), (10, 1))
        self.assertEqual((merge_count["output"], merge_count["sessions"]), (3200, 2))

    def test_a_transcript_whose_first_prompt_names_no_task_counts_for_its_records_task(
        self,
    ):
        cleared, pasted = (
            self.projects / "cleared.jsonl",
            self.projects / "pasted.jsonl",
        )
        # the owner's /clear in the pane of gift-note: the new transcript starts with his own words
        write(cleared, *HEAD, prompt("now make the note shorter"), reply("c1", 1, 7))
        # a launch line's path among other words names no task
        write(
            pasted,
            prompt(f"look at {launch('board-card-search')} and tell me"),
            reply("p1", 1, 5),
        )
        # beside them in the same log, a fork of board-card-search logged under gift-note, which counts for none of gift-note's
        fork = self.projects / "fork.jsonl"
        write(fork, prompt(launch("board-card-search"), "bg"), reply("f1", 1, 900))
        self.log(
            self.logged(SLUG, cleared, "clear"),
            self.logged(SLUG, fork, "fork"),
            self.logged(SLUG, pasted, "clear"),
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, SLUG), [str(cleared), str(pasted)]
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, "board-card-search"), [str(fork)]
        )
        self.assertEqual(lem_tokens.task_tokens(self.state, SLUG)["output"], 12)

    def test_a_transcript_that_is_gone_is_missing_for_its_records_task_only(self):
        self.log(self.logged(SLUG, self.projects / "gone.jsonl"))
        found = lem_tokens.task_tokens(self.state, SLUG)
        self.assertEqual((found["sessions"], found["missing"]), (0, 1))
        self.assertIsNone(lem_tokens.task_tokens(self.state, "board-card-search"))

    def test_a_fork_named_in_the_summary_of_an_ended_task_counts_for_the_open_task_its_first_prompt_names(
        self,
    ):
        own, merge, fork = (
            self.projects / f"{name}.jsonl" for name in ("search", "merge", "6fe214ec")
        )
        write(own, prompt(launch("board-card-search")), reply("a1", 1, 10))
        write(merge, prompt(launch("merge-leaves-board-lock")), reply("b1", 1, 200))
        write(
            fork, prompt(launch("merge-leaves-board-lock"), "bg"), reply("f1", 1, 3000)
        )
        # lem project prune made board-card-search's events one summary, which keeps their transcripts
        summary = {
            "ts": "2026-11-22T12:00:00Z",
            "event": "task.summary",
            "task": "board-card-search",
            "status": "landed",
            "transcripts": [str(own), str(fork)],
            "events": 40,
        }
        write(
            self.state / "events.jsonl",
            summary,
            self.logged("merge-leaves-board-lock", merge),
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, "merge-leaves-board-lock"),
            [str(fork), str(merge)],
        )
        self.assertEqual(
            lem_tokens.task_tokens(self.state, "merge-leaves-board-lock")["output"],
            3200,
        )
        self.assertEqual(
            lem_tokens.transcripts_of(self.state, "board-card-search"), [str(own)]
        )

    def test_the_first_prompt_names_a_task_only_when_it_is_a_launch_line_whole(self):
        self.assertEqual(
            lem_tokens.task_named(launch("merge-leaves-board-lock")),
            "merge-leaves-board-lock",
        )
        # the launch line of a task that ended names it still: the rule reads no state
        self.assertEqual(
            lem_tokens.task_named(
                "Read /Users/dev/my shop/.lem/state/tasks/old-task/session.md and follow it."
            ),
            "old-task",
        )
        for text in (
            None,
            "",
            "now make the note shorter",
            launch("gift-note") + " Then stop.",
            "Please " + launch("gift-note"),
            "Read /Users/dev/shop/tasks/gift-note/session.md and follow it.",
            "Read /Users/dev/shop/.lem/state/tasks/Gift_Note/session.md and follow it.",
        ):
            self.assertIsNone(lem_tokens.task_named(text), text)

    def test_the_first_prompt_is_the_first_user_record_that_is_not_meta(self):
        file = self.projects / "t.jsonl"
        write(
            file,
            *HEAD,
            "{half",
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": launch(SLUG)}],
                },
            },
            prompt("later words"),
        )
        self.assertEqual(lem_tokens.first_prompt(file), launch(SLUG))
        write(
            file,
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "image", "source": {}},
                        {"type": "text", "text": launch(SLUG)},
                    ]
                },
            },
        )
        self.assertEqual(lem_tokens.first_prompt(file), "")
        write(file, *HEAD)
        self.assertIsNone(lem_tokens.first_prompt(file))
        self.assertIsNone(lem_tokens.first_prompt(self.projects / "gone.jsonl"))


if __name__ == "__main__":
    unittest.main()

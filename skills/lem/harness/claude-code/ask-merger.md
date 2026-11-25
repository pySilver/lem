# Claude Code: ask-merger

A part of `../claude-code.md`, read when a landing starts the merge agent.

## ask-merger

One agent, started as an expert is (`ask-experts`), on the seat that `lem seat show SLUG merger`
prints: its `agent`, its `model` and its `effort`, each null when the seat leaves it out, which is
then the agent's own default, and `seat`, the line as written. `BRIEF` is the path the `next` of
`lem land merge-review SLUG` names (`paths`), the brief's `result.brief`, named by the proposed tip
and the base the read is against (`merge-brief-TIP-BASE.md` in the task directory); `ANSWER` is
the file beside it whose name says `answer` in the place of `brief`
(`merge-answer-TIP-BASE.md`), and `WORKTREE` the task's worktree. Give the agent that `BRIEF` and
no other: a brief of a later base is another read.

- `agent` is `claude`: the `Agent` tool with `subagent_type: "Plan"`, `run_in_background`, `model`
  the seat's model (left out when it is null, so the session's own model answers), `effort` only when
  the seat names one, and the prompt `Read BRIEF and follow it. Your reply is the review, and nothing
  else.` The `Plan` agent has no edit or write tool. Write its reply into `ANSWER` word for word,
  without the indent Claude Code puts before each line of a subagent's report.
- `agent` is `codex`: the `Bash` tool with `run_in_background`, on the `codex exec` line of
  `ask-experts` (`ask-experts.md`), with its quotes, this seat's `-m "MODEL"` only when it names a
  model and `-c "model_reasoning_effort=EFFORT"` only when it names an effort, and this step's
  `WORKTREE`, `ANSWER` and `BRIEF`.

**When the merge agent's agent gives an error**, one of the four of `second-opinion.md` (`missing`,
`login`, `tokens`, `model`): an exit of 127, `command not found` in `ANSWER.log`, or the agent's
own message of no login, no tokens or a usage limit, or a model it does not know, in `ANSWER.log`
or in the reply. A slow merge agent is no error: wait for it. Such an end is no review: record
nothing of it with `--file`, and run

```bash
lem seat failed SLUG merger --seat "LINE" --error KIND --said "ITS WORDS"
```

`LINE` being the `seat` that `lem seat show SLUG merger` printed, and `ITS WORDS` the agent's
line of the error. Its `result` names the fallback that stands in for the merger from now on
(`blocked` false, and its `seat`): say its `say` in one line, run `lem seat show SLUG merger` again,
which now prints the stand-in, and start the agent on that seat with the same `BRIEF` and
`ANSWER`, so that the task's record names the seat that read. Or its `blocked` is true: the task
is held `blocked` with the seat and the error, and "Waits for you" shows it; its pull request
stays open. Mark this session as waiting for the owner (`mark-waiting`) first, then say its `say`
in one line, the last text of your turn, and wait for his "go on": then `lem seat again SLUG`,
`lem seat show SLUG merger`, and the agent on the seat it prints, with the same `BRIEF`.

Any other non-zero exit, or no answer file, is a merge agent that did not answer: run `lem land
merge-review SLUG --no-answer --tip TIP --base BASE`, TIP and BASE as below. It counts as a reply
the step refuses: the first is refused, and the agent starts once more on the same `BRIEF` and
`ANSWER`; the second end of that brief is recorded as a second refused reply is (below), and its
`next` says what follows.

Then `lem land merge-review SLUG --file ANSWER --tip TIP --base BASE`, TIP and BASE being the
`tip` and the `base` of the brief's `result`, which the command of its `next` already holds. A
reply the step refuses (no verdict, or no call on a moved base) is a new start of the agent on the
same `BRIEF` and `ANSWER`. A second refused reply of that brief is recorded: on a moved base as
`another round`, and on a base that did not move as a read that calls the owner, with no verdict,
so "Waits for you" shows him "Read the merge review"; start no agent again for that tip and base.

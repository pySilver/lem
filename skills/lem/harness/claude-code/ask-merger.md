<!-- lem: old form -->
# Claude Code: ask-merger

A part of `../claude-code.md`, read when a landing starts the merge agent.

## ask-merger

One agent, started as an expert is (`ask-experts`), on the `seat` that `lem land merge-review SLUG`
printed: its `agent`, its `model` and its `effort`, each null when the seat leaves it out, which is
then the agent's own default. `BRIEF` and `ANSWER` are the `brief` and `answer` paths the step
printed, each named by the proposed tip and the base the read is against
(`merge-brief-TIP-BASE.md`, `merge-answer-TIP-BASE.md`), and `WORKTREE` its `worktree`. Give the
agent that `BRIEF` and no other: a brief of a later base is another read.

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
lem project seat-failed SLUG merger --seat "LINE" --error KIND --said "ITS WORDS"
```

`LINE` being the `seat` that `lem land merge-review SLUG` printed, and `ITS WORDS` the agent's
line of the error. It prints a seat to open, the fallback that stands in for the merger from now
on: say its `say` in one line, run `lem land merge-review SLUG` again, which writes the brief of
the same tip and base again and keeps the stand-in's seat with it, and start the agent on the
`seat`, the `brief` and the `answer` that this second run printed, so that the record names the
seat that read. Or it prints `blocked: true`: the task is `blocked` with the seat and the error,
and "Waits for you" shows it; its pull request stays open. Mark this session as waiting for the
owner (`mark-waiting`) first, then say its `say` in one line, the last text of your turn, and wait
for his "go on": then `lem project seat-again SLUG`, `lem land merge-review SLUG` again, and the
agent on the seat it prints.

Any other non-zero exit, or no answer file, is a merge agent that did not answer: run `lem land
merge-review SLUG --no-answer --tip TIP --base BASE`, TIP and BASE as below. It counts as a reply
the step refuses: the first is refused, and the agent starts once more on the same `BRIEF` and
`ANSWER`; the second end of that brief is recorded as a second refused reply is (below), and its
`next` says what follows.

Then `lem land merge-review SLUG --file "ANSWER" --tip TIP --base BASE`, TIP and BASE being the
`tip` and the `base` the step printed with the brief. A reply the step refuses (no verdict, or no
call on a moved base) is a new start of the agent on the same `BRIEF` and `ANSWER`. A second
refused reply of that brief is recorded: on a moved base as `another round`, and on a base that did
not move as a review that calls the owner, with no verdict, so "Waits for you" shows him "Read the
merge review"; start no agent again for that tip and base.

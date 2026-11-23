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
  `WORKTREE`, `ANSWER` and `BRIEF`. A non-zero exit, or no answer file, is a merge agent that did
  not answer: start it once more. After a second such end on a base that did not move (`moved` of
  the brief's facts is null), tell the owner in one line that the task waits for his read. On a
  moved base, land the task again as `stages/land.md` says for a read that said another round
  ("the base moved" of step 8), and tell the owner nothing of a read: in doubt, the checks run
  again.

Then `lem land merge-review SLUG --file "ANSWER" --tip TIP --base BASE`, TIP and BASE being the
`tip` and the `base` the step printed with the brief. A reply the step refuses (no verdict, or no
call on a moved base) is a new start of the agent on the same `BRIEF` and `ANSWER`. A second
refused reply of that brief is recorded: on a moved base as `another round`, and on a base that did
not move as a review that calls the owner, with no verdict, so "Waits for you" shows him "Read the
merge review"; start no agent again for that tip and base.

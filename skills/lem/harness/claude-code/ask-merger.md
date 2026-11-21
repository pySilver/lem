# Claude Code: ask-merger

A part of `../claude-code.md`, read when a landing starts the merge agent.

## ask-merger

One agent, started as an expert is (`ask-experts`), on the `seat` that `lem land merge-review SLUG`
printed: its `agent`, its `model` and its `effort`, each null when the seat leaves it out, which is
then the agent's own default. `BRIEF` and `ANSWER` are the `brief` and `answer` paths the step
printed, and `WORKTREE` its `worktree`.

- `agent` is `claude`: the `Agent` tool with `subagent_type: "Plan"`, `run_in_background`, `model`
  the seat's model (left out when it is null, so the session's own model answers), `effort` only when
  the seat names one, and the prompt `Read BRIEF and follow it. Your reply is the review, and nothing
  else.` The `Plan` agent has no edit or write tool. Write its reply into `ANSWER` word for word,
  without the indent Claude Code puts before each line of a subagent's report.
- `agent` is `codex`: the `Bash` tool with `run_in_background`, `-m MODEL` only when the seat names a
  model and `-c model_reasoning_effort=EFFORT` only when it names an effort:

  ```bash
  codex exec -m MODEL -c model_reasoning_effort=EFFORT -s read-only --skip-git-repo-check --ephemeral -C WORKTREE -o ANSWER - < BRIEF > ANSWER.log 2>&1
  ```

  A non-zero exit, or no answer file, is a merge agent that did not answer: start it once more, and
  after a second such end tell the owner in one line that the task waits for his read.

Then `lem land merge-review SLUG --file ANSWER --tip TIP`, TIP being the `tip` the step printed with
the brief.

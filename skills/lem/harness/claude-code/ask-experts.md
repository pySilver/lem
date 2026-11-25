# Claude Code: ask-experts

A part of `../claude-code.md`, read when a session starts the experts.

## ask-experts

Start the experts in one message. Read `BRIEF`, `WORKTREE` and each answer file from the
`result` of `lem experts brief`.

Each entry of the `experts` list that `lem experts brief` printed is one expert to start, from the
settings' `seats.experts` or from the brief's `--seat`: its `name`, which is the `--expert` word of
`lem experts record`, its `agent`, `model` and `effort`, and its `answer` file. The settings refuse
an expert's seat with no model or no effort; only a `--seat` may leave one out, and its value is
then null.
Start each by its agent, and never with a model or an effort the entry does not name:

- an entry whose `agent` is `claude`: the `Agent`
  tool with `subagent_type: "Plan"`, `model` the entry's `model` (left out when it is null), `effort`
  the entry's `effort` only when it names one, and the prompt
  `Read BRIEF and follow it. Your reply is your answer, in the form the brief's last section
  gives, and nothing else.` The `Plan` agent has no edit or write tool, so it reads; it has Bash,
  so the brief's "change no file" is what keeps it from a write there. It runs in the
  background, and its reply reaches you as its message: write that reply into its answer file
  word for word, without the indent Claude Code puts before each line of a subagent's report,
  then record it with `lem --repo WORKTREE experts record --folder FOLDER --expert NAME`.
- an entry whose `agent` is `codex`: the `Bash`
  tool with `run_in_background`, on this line, with `-m "MODEL"` only when the entry names a model
  and `-c "model_reasoning_effort=EFFORT"` only when it names an effort:

  ```bash
  codex exec -m "MODEL" -c "model_reasoning_effort=EFFORT" -s read-only --skip-git-repo-check --ephemeral -C "WORKTREE" -o "ANSWER" - < "BRIEF" > "ANSWER.log" 2>&1
  ```

  Keep the double quotes around each value you put in: a checkout under a folder such as
  `Client Work` holds a space, which splits a bare path into two words. `-` reads the prompt from
  stdin, and the brief file is that stdin, so it ends: a Codex in the background whose stdin stays
  open waits for input and never starts (seen 2026-11-16, a headless Codex review). `-o` writes its last message into the answer file. You are told when the command
  exits; then record the answer with the same command. A non-zero exit, or an answer file that is
  not there, is an expert that did not answer: the skill's step 3 says what follows.

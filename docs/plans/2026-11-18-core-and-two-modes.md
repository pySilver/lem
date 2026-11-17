# The core, and a task that runs with the owner or alone

Status: a plan, not built. It follows the owner's interview of 2026-11-17 and 2026-11-18
(`AGENTS.md`, "His interview ... on what stays in Lem").

## What the owner gets

1. A smaller Lem. Its core is the path from a request to a merged pull request. Four commands
   leave, and two parts go out of sight.
2. Two ways to run a task. **With you**: you see the criteria and each decision before the build.
   **Alone**: no step waits for you, and you get two pages at the end. You switch with "go alone"
   and "I am back", at any stage.
3. One way to decide in doubt: a ladder of opinions. A count decides, not a model.
4. A night run that ends as a pull request.

## What a small change pays for this

Nothing. A small change has no decision and no plan, so it reads no new text and starts no new
agent. It gets no pages: its pull request text is enough. This is checked at the end by a count
of the words its path reads (`wc -w`), against the count before.

## What exists already

Most of this is a new shape for parts that exist. That keeps each task small.

| The owner asked for | What exists today |
| --- | --- |
| personas first for a decision | the lead runs the panel before it asks (`stages/build.md`, `stages/plan.md`) |
| the experts in doubt | `lem-ask-expert`, `lem decisions advise`, `settle --away` |
| a decision taken without him is named | `decisions.jsonl`, and the "not green" line of the pull request |
| the gate | `lem-gate`, in shadow mode at Lem's card (`stages/choice.md`) |
| a run with nobody there | `/lem night`, which stops at a plan today |
| a page made by agdoc | agdoc is a recommended tool of the machine check |

## The tasks

Each task is one builder's job, or a short chain of builders. Each ends with its test blocks
green. The stage texts have no unit test: the real runs at the end are their proof.

### 0. The shorter texts reach main first

The branch `polish/diet` splits `stages/new.md` by path. Every later task edits those files, so it
lands first. Proof: one real small change and one real full change in the scratch repository.

### 1. What leaves, and what goes out of sight

- `lem-release`, `lem-last-tag` and `lem-pr-review` leave the repository, with their scripts,
  their names in `bin/lem`, their tests, their rows in the README and their part of `NOTICE`.
- `/lem gate` and `/lem nap` are no commands of the owner's. The gate's skill stays for task 3.
- Naps make no page: the Dreams tab, its pictures and its place in the README go. A nap still
  writes its note for the retro. `[naps]` stays one row of the settings page.
- agdoc moves from "recommended" to "required" in the machine check and the install page.

Proof: `tests/lem-command.sh` and `tests/lem-machine.sh`; a search of every text for a name that
is gone.

### 2. The mode of a task

- A task's record holds its mode: with the owner (the default) or alone.
- The owner's words: "go alone" for one task, "go alone for all" for every open task, "I am
  back" to take it off for the steps that remain. `lem project` writes it and logs who said it.
- Alone means: Lem takes its own guess for each interview question and logs it as a decision. It
  approves the criteria itself. Each decision takes the ladder of task 3 with no wait.
- Two things wait in either mode: a step that a later "no" cannot reverse, and the merge.
- A pull request of a task that ran alone is not green, and its first line says what the owner did
  not approve.
- With the owner, a card that he does not answer in `flow.decision_wait` minutes goes on as if
  the task ran alone for that one decision. This is today's rule, in the new words.
- `settle --away` and the "away on two facts" rule go: the flag is his word that he is away.

Proof: tests of the flag and of what the landing says for a task that ran alone, in
`tests/lem-settings.sh`, `tests/lem-decisions.sh` and `tests/lem-land-review.sh`.

### 3. The ladder of opinions

One path for every decision that is not plainly the lead's own, in the plan and in the build:

0. **The gate.** Did the owner rule on it (the rulings folder)? Can a test or a rule answer it? Is
   it cheap and can it be reversed? Then it is decided there, and logged as the gate's.
1. **The lead** writes the options, its pick and the facts.
2. **The personas** answer. All for the pick: taken.
3. **The dialectic**, when they split: two subagents of the lead, one for and one against the
   option with the most votes. A clear result: taken.
4. **The experts**, when it is not clear: two model families. Both for one option: taken.
5. Else the lead's pick stands, and the pull request is not green for it.

- "All opinions", the owner's words, runs every level for one decision.
- Each level logs whether it changed the pick. After real decisions, the log shows which level
  never changes anything.
- With the owner, the result of the ladder is the card he sees before the build goes on. Alone,
  nothing waits.
- The Jev model is no part of it. It stays where it works: the correction queue.

This replaces the card with the experts' advice at the start of the wait, and the gate's shadow
mode. `lem decisions` loses `advise` and `settle`, and gains the level of each record.

Proof: `tests/lem-decisions.sh` and `tests/test-ask-expert.sh`, with stand-ins for every agent.

### 4. The two pages at the end

- `decisions.md` in the task's folder: each decision, who took it (the gate, the lead, the
  personas, the dialectic, the experts, the owner), the options and the reason.
- `built.md` beside it: what was asked, what was built, and why. Short enough to read in a minute.
- Each opens with a red block when something waits for the owner: a step that cannot be
  reversed, criteria he did not approve, a decision that no level settled.
- Neither file is committed. The pull request text carries the short form for a teammate.
- At the pull request, Lem makes one agdoc page from the two files. `/lem status <task>` opens it.
- A small change gets neither.

Proof: a test that `land.py` writes both files from a task's records, with the red block in each
case; the page itself is seen in the real runs.

### 5. The night run ends as a pull request

- `/lem night` takes backlog items, the smallest first, up to `flow.max_tasks`. Each runs alone
  to its pull request.
- It leaves out, as today, an item in reach of what must never go wrong, and an item that
  another branch holds.
- The brake counts night pull requests that nobody merged yet, where it counted drafts.
- The morning list of `/lem` shows them as pull requests, with the night's report.
- A draft of the form before still shows in the list and can be approved or rejected.

Proof: `tests/lem-settings.sh` for the list of what waits; one real night in the scratch
repository.

### 6. The texts for people

The README, `docs/flow.md`, `docs/settings.md`, `docs/inside.md` and `docs/install.md` say the
above, in ASD-STE100, and are checked against the code. The README's table of commands gets
shorter, and it gains the three sentences that the owner types to switch the mode.

## Order

0, then 1. Then 2 and 3 as one chain, because they change the same files. Then 4, 5, 6. One
builder at a time in a file set. A builder runs only the test blocks it touches. The maintaining
session runs the full suite once before each move of `main`.

## The real runs that end it

In the scratch repository, with the owner or with the session as its operator (said plainly in
the report, and with the correction queue off for that computer):

1. A small change, to its pull request. The count of what its path reads.
2. A full change with the owner: the interview, the criteria, one decision on a card.
3. The same kind of change with "go alone" said after the interview. The two pages.
4. One night.

`main` moves after 0 and 1, and again after the rest.

## Not in this plan

GitHub Issues as a tracker, the add-ons (`docs/backlog/add-ons-after-the-core.md`), Codex in each
role, and the first task in mybaze. The dialectic in a companion with a seat of its own waits for
the log of task 3 to show that the dialectic changes picks.

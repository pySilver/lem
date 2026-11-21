# The core, and a task that runs with the owner or alone

> **Status: built** on 2026-11-18, in the commits from `e3fb4b9` to `3f9f4da`. The core, the ladder,
> the fewer settings and the night as pull requests still hold; the redesign of 2026-11-20 ([2026-11-20-a-session-for-each-task.md](2026-11-20-a-session-for-each-task.md)) replaced the two
> modes and the cards: the build asks the owner nothing, his away status is one mark of the
> machine, and a task lives in a session of its own. It follows the owner's interview of
> 2026-11-17 and 2026-11-18 (`docs/rulings/`, "His interview ... on what stays in Lem").

## What the owner gets

1. A smaller Lem. Its core is the path from a request to a merged pull request. Four commands
   leave, and two parts go out of sight.
2. Two ways to run a task. **With you**: you approve the criteria, Lem tells you each decision
   in one line when it is taken, and a decision in real doubt comes to you as a card. **Alone**:
   no step waits for you, and you get two pages at the end. You switch with "go alone" and "I am
   back", at any stage.
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
- `/lem ask` is no command of the owner's either. The question page stays Lem's own, and Lem
  opens it by itself each time it asks.
- `/lem annotate` leaves. webrev becomes a required recipe, and Lem opens a plan or a document
  with it. The setting `tools.annotate` goes with the `[tools]` table (task 1b).
- The `lem-backlog` skill leaves, with its sorting script. The agterm cookbook's backlog recipe
  (its `backlog` skill and its picker) becomes required in its place. The item format is the
  same: one file for each item in `docs/backlog/`, with `worth`, `where` and `added`. Lem's
  builders keep filing items on the task's branch, and the stage texts say the format in two
  lines, so no stage needs the skill. The night run reads the items itself. The board's Backlog
  tab stays, with its one action that gives an item to Lem as a request.
- Naps make no page: the Dreams tab, its pictures and its place in the README go. A nap still
  writes its note for the retro. `[naps]` stays one row of the settings page.
- agdoc, webrev and the backlog recipe move to "required" in the machine check and the install
  page.

Proof: `tests/lem-command.sh` and `tests/lem-machine.sh`; a search of every text for a name that
is gone.

### 1b. Fewer settings

The owner doubts that every section of the settings should stay. Today the settings page lists
40 keys (the maintaining session's count of `docs/settings.md`). After this task it lists 25, and
a new project writes two of them by hand: the test command and what must never go wrong.

| Section | Today | After | What goes, and where the value lives then |
| --- | --- | --- | --- |
| `[paths]` | 10 | 2 | Only `plans` and `plan_file` stay. Lem's own files have one place: `.lem/profile.md`, `.lem/personas`, `.lem/lessons.md`, `.lem/worktrees`. The rules for the code are the harness's folder, `.claude/rules`. The review tool's folder is `.revmux`. The backlog is `docs/backlog`, as the cookbook's recipe has it. The rulings are `docs/rulings`. |
| `[checks]` | 5 | 3 | `commands`, `setup` and `alone` stay. `ignores` and `bar` go. |
| `[flow]` | 4 | 3 | `watch_seconds` goes: the watch looks each 60 seconds. |
| `[tools]` | 2 | 0 | The whole table goes: Lem asks with its page and opens a text with webrev. |
| `[naps]` | 3 | 1 | Only `on` stays. A nap's folder is kept 30 days, and 6 hours pass between two naps. |
| `[branch]`, `[seats]`, `[corrections]`, `[tracker]` | 16 | 16 | No change. |

- **The rules for the code are not Lem's.** Claude Code loads `.claude/rules` by itself. Lem only
  names the matching rule files to the agents that load nothing by themselves: Codex, and the
  agents of the review tool. `/lem init` writes no style guide, and the catalog of published
  style guides leaves.
- **`[checks]` stays, because "green" must be a fact.** A linter and a type checker are a git
  hook's job, and the page says so. A test suite is not: a hook must be fast. Lem's script runs
  the test command itself, so "green" is what a script saw, not what an agent says.
- **Three words that sound alike get one line each on the settings page.** Rules: how code is
  written here (`.claude/rules`). Lessons: how the agents work here (`.lem/lessons.md`).
  Rulings: what the owner decided about the product (`docs/rulings`).
- A settings file that still has a key that is gone is refused once, with every line to delete,
  as the tables of an older Lem are today. A task that is open keeps reading its own copy.
- `/lem init` no longer offers to link a folder that another tool keeps. A project that has its
  personas or its profile in another place moves them into `.lem/`.

Proof: `tests/lem-settings.sh`; `docs/settings.md` one to one with `lem project show` and the
template; the scratch repository's own settings file goes through the refusal.

### 1a. Tests that are useful and fast

The owner: "Please make all kind test actually useful and not painfully slow."

Today (the maintaining session's run of 2026-11-17): 623 checks in 20 suites, 408 seconds on the
clock, 3,897 seconds summed over the suites. One call of a script costs about 170 ms, and most
checks make several.

- **Useful.** A check stays when it turns red for a thing a developer would notice: a wrong
  state, a wrong refusal, a lost commit, a false "green". A check that only pins the words of a
  message pins one key word, or goes.
- **Fast.** A check of pure logic runs inside one Python process, not as one process for each
  call. A block copies its throwaway repository from a template, where it builds one with git
  commands today. The Chrome suites and `shellcheck` run only when their files changed.
- **Picked.** One script names the blocks for the files a change touched. A builder runs those.
  The full suite runs once before `main` moves.
- Targets, both estimates until measured: a builder's blocks in under 30 seconds, the full suite
  in under 2 minutes on this Mac.

Proof: ten behaviors broken by hand, one at a time (the list is in the task's report). Each must
turn a check red before the change and after it, so the speed did not cost what the tests guard.

### 2. The mode of a task

The design to build is the smaller one of two: `2026-11-18-core-and-two-modes/mode-and-ladder.md`
beside this file. A first design added six commands and a script that checked what agents wrote;
a second opinion called it machinery, and the maintaining session took the smaller one.

- A task's record holds its mode: with the owner (the default) or alone. The command is `lem
  project mode`, because `lem project alone` is the lock for tests that need the machine. Texts
  for people say "without the owner".
- The owner's words: "go alone" for one task, "go alone for all" for every open task, "I am
  back" to take it off for the steps that remain. The event logs who said it.
- Alone means: Lem takes its own guess for each interview question and logs it as a decision. It
  approves the criteria itself. Each decision takes the ladder of task 3 with no wait.
- Two things wait in either mode: a step that a later "no" cannot reverse, and the merge. An
  agent never merges while a task runs alone, whatever `branch.land` says.
- A pull request is not green when something of the owner's was decided without him: criteria he
  did not approve, or a decision that went past the personas. Its first lines say which part ran
  without him. A task that ran alone with nothing of his decided without him is green.
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
2. **The personas** answer. Two or more votes, all for the pick: taken. An answer with no clear
   pick blocks, and is never dropped.
3. **The dialectic**, when they split: two subagents of the lead, one for and one against the
   option with the most votes. The one against names breaks with file and line, and the lead
   opens each. No confirmed break: taken. A confirmed break goes to the experts as a fact.
4. **The experts**, when it is not clear: two model families. Both for one option: taken.
5. Else the lead's pick stands, marked as not settled.

- The rules are one stage text, read only when a decision is in doubt. The lead applies the
  counts. A script checks one thing: two persona votes or more, all for the option taken.
- A decision that went past the personas is not green when the owner did not answer it.
- "All opinions", the owner's words, runs the levels that did not run yet for one decision.
- Each record says which level settled it and what each level answered. After real decisions,
  the records show which level never changes anything.
- With the owner: a decision that the gate or the personas settled gets no card. Lem says each
  decision once in the conversation, in one line, and waits for nothing. A decision that went
  past the personas is a card before the build goes on. Alone, nothing waits.
- The Jev model is no part of it. It stays where it works: the correction queue.

This replaces the gate's shadow mode with its log, and `settle --away`. A choice shows on the
board when it is taken, not while it climbs.

Proof: `tests/lem-decisions.sh` and `tests/test-ask-expert.sh`, with stand-ins for every agent.

### 4. The two pages at the end

- `decisions.md` in the task's folder: each decision, who took it (the gate, the lead, the
  personas, the dialectic, the experts, the owner), the options and the reason.
- `built.md` beside it: what was asked, what was built, and why. Short enough to read in a minute.
- Each opens with a red block when something waits for the owner: a step that cannot be
  reversed, criteria he did not approve, a decision that no level settled.
- Neither file is committed. The pull request text carries the short form for a teammate.
- At the pull request, Lem makes one agdoc page from the two files. `/lem status <task>` opens it.
  The owner saw a sample (agdoc's "classic" design, the red block first on the screen) and said
  "sample page is fine" (2026-11-18). The sample and the shapes of the two files are in
  `2026-11-18-core-and-two-modes/pages/`.
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
above, in ASD-STE100 and American English, written for readers who are not native speakers. They
are checked against the code, and then proofread by an agent briefed for those readers, as the
README was. The README's table of commands gets shorter, and it gains the three sentences that
the owner types to switch the mode.

## Order

0, then 1, then 1b, then 1a, so that every later builder has the fast tests and the fast tests
are not written for settings that go. Then 2 and 3 as one chain,
because they change the same files. Then 4, 5, 6. One builder at a time in a file set. A builder
runs only the test blocks it touches. The maintaining session runs the full suite once before
each move of `main`.

The owner can use Lem while this is built: `main` works today, and each move of `main` is one
update of the plugin.

## The real runs that end it

In the scratch repository, with the owner or with the session as its operator (said plainly in
the report, and with the correction queue off for that computer):

1. A small change, to its pull request. The count of what its path reads.
2. A full change with the owner: the interview, the criteria, one decision on a card.
3. The same kind of change with "go alone" said after the interview. The two pages.
4. One night.

`main` moves after 0, 1, 1b and 1a, and again after the rest.

## Not in this plan

GitHub Issues as a tracker, the add-ons (`docs/backlog/add-ons-after-the-core.md`), Codex in each
role, and the first task in mybaze. The dialectic in a companion with a seat of its own waits for
the log of task 3 to show that the dialectic changes picks.

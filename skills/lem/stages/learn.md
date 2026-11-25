# learn and retro

What Lem remembers of a repository is there for one thing: the next task costs the owner less
attention than the last one did, because a correction is not needed twice, a question is not
asked twice and a wrong read is not made twice. Whatever serves that is worth a line, a failure or
a thing that worked; what an agent can read off the code or the records at the moment it needs it
is not. A line is a claim about the repository, and a claim can be wrong from its first day or
go stale as the code moves, and it is then read and trusted like the others: so the record of what
happened stays the judge of every line ("The components of agent memory", Anthropic, 2026-11-06).

A correction holds when it changes the text an agent reads at the moment it does the step. A note
read at session start does not: one note was opened before the step it governs in 2 of 42
sessions, and the owner gave that correction again to eight sessions in two minutes (mybaze,
2026-11-12). A rule loaded at session start lost to a skill template that said otherwise.

## learn, in the session

When the owner corrects you, disagrees with an approach, or tells you something for the second
time ("again", "I told you", "we discussed"), do this in the same reply, before going on. The
owner may correct a task's session, its lead or, in a plan talk's pair, its defender; whoever was
corrected does it:

1. **Say the lesson in one sentence** an agent could follow next time.
2. **Find the file that owns the step**, the first that fits:
   - a step of a skill (a page it builds, a message it sends, a command it runs). A skill the
     repository holds itself: that skill's file, a project file like any other. Lem, or another
     skill installed from outside the repository: one line in the project's lessons file
     (`lem path lessons`) that opens with the stage's or the skill's name (`new: ...`),
     which Lem reads before each subcommand. Never the installed skill's own file, whether it is
     a link to a clone or a plugin's copy: that file is the same for every repository that uses
     it, an edit there is live in all of them at once with no review, and a plugin's next update
     drops it. Your report says that the line is a lesson about Lem itself, so the owner can
     bring it to whoever maintains Lem;
   - how code is written here: the rule file of `.claude/rules` whose scope covers it
     (`lem path rules`);
   - what a person of the project wants or notices: that persona's file
     (`lem path personas`);
   - what a review should catch or stop raising: the lens, the review profile or the
     rejected-findings list (`lem path review`). That folder is the review tool's own:
     Lem never moves, links or reshapes it, and a lesson still writes a line into a file there;
   - a decision about the product that outlives the task: a ruling, one bullet of the rulings
     list (`lem path rulings`), written as "A ruling" below says;
   - a command shape a pattern can match: a hook or a commit check of the repository that refuses
     it and names the replacement;
   - none of these: one line in the project's lessons file (`lem path lessons`), which the
     plan and build stages read.
3. **When the owner asked for the change, make it** and say, for each file you changed, its path,
   what changed and why, in one to three lines a file. When you found the lesson yourself, show
   the edit with the same three things and make it on the owner's "apply". No file a lesson
   changes goes unnamed, whichever folder holds it.
4. A lead commits a project file on the task's branch with the work. A session with no task's
   branch (a session of no task): there the edit of a project file is a task of its own
   (`/lem new`), so it lands through the checks like any change. A retro changes no file at all:
   what it finds is a proposal ("retro" below). Every file a lesson changes is in this repository, the review tool's
   folder included: never a file in the home directory, and no session commits in another
   repository. A retro started in one repository once committed an edit of a stage on the
   checked-out base branch of the clone the skill was linked from, with nobody's review, and the
   next push from that clone published it (2026-11-17).

A lesson about one project never goes into a skill, and the lessons file never holds what a style
guide file, a persona or a lens could hold: it is the last target, and it stays short enough to be
read whole. Every session reads it before each subcommand, so each line of it is paid for at every
step and a wrong one is carried into every task: when it grows, move a line's detail down into the
file that owns its step, or into a ruling, and leave the one sentence that points there.

## A ruling

A project's rulings are one list, the file `lem path rulings` prints, and a ruling is one
bullet of it under the `##` heading of its group: the rule in one sentence in bold, then the day
the owner ruled it in parentheses. The owner approves "a refund never makes an invoice negative"
on 2026-11-22, and the list gets, under `## Invoices`:

```markdown
- **A refund never makes an invoice negative.** (2026-11-22)
```

- **Only on his approval.** A bullet is written only when the owner approved that ruling: in a
  session on his "apply" (step 3), or in a task he started from a backlog item that proposes it
  (a retro's proposal reaches him only so). A ruling never goes in as a first-time lesson nobody
  was asked about.
- **Its group.** Put it under a heading the list has when one fits. When none does, add the
  group's `##` heading at the end of the list, with the bullet under it. A list that does not
  exist yet is made with its `#` title, `# The owner's rulings`, and the group's heading.
- **One ruling in force for each question.** A ruling that replaces one of the list takes its
  bullet's place, and one that changes a part of another changes that bullet's words: the list
  never holds two rulings that disagree. A bullet leaves the list only on the owner's word.
- **Its words.** Where the sentence alone could mislead, at most three lines after it say how far
  it reaches, his words in quotes only where they are the rule or its limit. No history in a
  bullet: git keeps the old words.

## retro

`/lem retro` changes no file and asks the owner nothing, whether a scheduled job started it or he
typed it. What it finds is a proposal, a fresh reviewer reads each proposal before he does, and
what passes reaches him only as an item of the board's "Backlog", which he starts as a task or
drops. A first-time lesson is a proposal too, and so is a ruling ("A ruling"): a retro records
no lesson by itself.

1. **Since when.** `lem proposals list` gives, as `newest.retro.at`, the time of the
   newest run of the retro: this one reads what came after it, and with null (the first retro)
   all that the state folder keeps. The night's proposals since then (`undecided`, of the kind
   `night`) and every one already `refuted`, `passed` or `dropped` are what it does not propose
   again. When the read refuses, it names the file and the fix: say that line and stop there,
   with no close, so that the session waits for the owner with it.
2. **What it reads**, since then: each task's decisions (`lem decisions list SLUG`: who took each,
   a pick past the personas, a breaker and the owner's help on it), the "not verified" and
   "outside defects" lines of each `report.md`, and each task's record
   (`.lem/state/tasks/SLUG/task.json`). Read `landing.proposed` for the latest proposal's
   `at`, `green` and `reasons`. In `journal`, read `review-round` entries for
   `review.counts` and `review.answered`, `not-green` entries for `tip` and `reasons`,
   and `careful-missed` entries for `round` and `why`. Use each entry's `at` for the date
   of the read. Read the owner's corrections from the
   project's correction queue when it keeps one (below). When nothing of an ended task happened for
   `state.keep_days` days, `lem prune` folds its journal into one summary entry, which holds none
   of those entries (only the newest proposal's green and reasons), and removes every file of the
   task but its record, its sessions, its ask and its ticket: no `report.md` stays. So a retro more
   than that apart from the one before reads only the newer tasks' reports, decisions and events.
3. **What it looks for**: what came back, and each finding is one proposal.
   - a correction the owner gave more than once: the record it had did not reach the step;
     propose its move with step 2 above, the file that owns the step and the change;
   - a decision the owner overturned: the rule that would have decided it right, as a ruling or a
     rule line;
   - a task the owner made careful after its lead called it plain, a `careful-missed` entry, or a
     defect a review found in a plain task. First find which it was. A topic named it, and the
     lead read the plan wrong: the lesson is about that judgment, and it may be sharper words for
     the topic. No topic named it: propose one sentence for `flow.topics`; the settings change
     only in a task the owner starts from its item;
   - a review finding that repeats across items: a rule line or a check, so the builder meets it
     before the review does;
   - a check or a step of this skill that cost time and changed nothing: propose to remove it,
     with the turns that show the cost;
   - a lesson the days no longer bear out. Read each line of the project's lessons file, and each
     lesson an earlier retro recorded (`lem corrections lessons`, with the file it went to),
     against the records since it was written: the thing it names is gone, the tasks went the
     other way and nobody objected, or the owner said the opposite later. Propose its removal or
     its new words, with the task that shows it. A lesson is never removed because it is old. A
     lesson recorded `proposed` is in no file yet, so it is never one to remove: when the owner
     gave it again, it is a lesson that came back;
   - a choice that climbed past the personas and held: the same question decided by the dialectic
     or the experts in two tasks or more, or one such pick that the owner kept when he read its
     pull request. The next task pays for that climb again unless the answer is where the first
     level finds it, so propose it as a ruling, a bullet of his rulings list, with both tasks. A
     pick of the experts is no ruling of his until he starts the task of its item;
   - a lesson the records show once, a correction or a finding: propose it too, the file that owns
     its step and the sentence.

   Where the project has naps (`stages/nap.md`), the retro also reads their waking notes,
   `naps/*/waking.md` in the folder `lem path state` prints, of each nap whose time, the
   start of its folder's name, is after `newest.retro.at`. A waking note is one agent's impression
   after a dream, so it is a candidate and never a lesson: a thing a note names becomes a proposal
   only when the tasks' records above show it too, and that proposal names the note in its
   `source`, by the folder's name. The same holds for a lesson a note says no longer fits the
   days: it is a candidate for the removal above, checked against the records like any other. A
   note is never a proposal by itself, and the dream beside it is not read for lessons.
4. **Add the run** to the day's file, also when it proposes nothing, on stdin as a quoted heredoc:

   ```bash
   lem proposals add --kind retro --file - <<'JSON'
   {"read": "the tasks gift-note and refund-total since 2026-11-23T06:55:00Z, 3 correction groups, the waking note of the nap 2026-11-23-1410", "proposals": [
     {"area": "lessons", "move": "A builder runs the migrations before the tests", "body": "the file, the change, and the case in the owner's words", "source": "the tasks gift-note and refund-total; correction group 1a2b3c4d", "where": ".claude/rules/testing.md"}
   ]}
   JSON
   ```

   `read` says what this run read, so that a run of no proposal (`"proposals": []`) still says
   what it looked at. Each proposal has exactly these five keys: `area` (lower-case words joined by
   hyphens), `move` in one line, `body` (the file, the change and the case), `source` (the records
   it rests on, each by its name: a task, a report, an event, a nap's folder, a correction group)
   and `where` (the file it would change, `PATH` or `PATH:SYMBOL`). The command writes
   `retros/YYYY-MM-DD.json` in the state folder, or adds after the runs already there, and its
   result's `names` gives each proposal's name (`retro of 2026-11-24 #3`).
5. **The correction queue's records**, when the project keeps a queue: record each group as "The
   correction queue" below says, a lesson with the name of its proposal.
6. **The reviewer**, when `lem proposals list` now gives an `undecided` proposal of any
   day: `spawn-builder` with the brief

   ```
   Read `skills/lem/prompts/proposals.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check.
   checkout: the main checkout's absolute path
   ```

   It judges each proposal with no verdict, the night's too, against the bar of rule 6 of the
   builder's standing rules, refutes the weak ones with their reasons, each kept as a `worth: no`
   item of the state folder's `backlog/`, and writes the rest as items there, one for each area,
   all through `lem proposals verdict`. Wait for its reply, which is its report. With no `undecided` proposal, no reviewer
   starts.
7. **The closing report**: what the run read, each proposal's name and move, and from the
   reviewer's report each refuted one with its reason and each item with its path and title. It
   names no changed file, since the retro changed none.
8. **The end.** `run-in-background` with `lem session close-job`, as the last step, after the
   reviewer's reply. It closes the session once the owner is not looking at it. A refusal says
   that the session is the owner's (no job started its agent for this run) or a task's: say its
   line, and the session stays open. Two answers say that there is nothing to close, and the run
   ends: exit 0 with `"closed": false`, "the session ID is no longer in agterm's tree", and the
   refusal "no session to close", for a run with no agterm session (a `claude -p` from a plain
   shell).

## The correction queue

An optional part. A session that is corrected does not always record it, and a correction that
is given again is what a retro is for. So a project may keep a queue: a hook asks a small
decision model about each message the owner types, and queues the ones an agent should learn a
lesson from. The machine's own file turns it on, for every repository on that machine (`collect`
under `[corrections]` of `~/.config/lem/machine.toml`), and `stages/init.md` says how the owner
agrees to it. `lem settings show` says whether it is on, as `corrections.collect`. When it is off, skip this
section.

```bash
lem corrections list      # unreviewed groups, most sessions first
lem corrections show ID   # one group in full
lem corrections lessons   # what earlier retros recorded
```

1. **Failures first.** `list` gives `failures`: messages the hook could not judge (no key, a
   failed request). Say the count and the newest error before anything else.
2. **A group** is every unreviewed entry with the same words of the owner, so one sentence sent
   to eight sessions is one item with its count. The small model is a loose filter on purpose:
   about three of four of its flags were not lessons in the sample its threshold comes from
   (the queue's question in Lem's source, `addons/corrections/question.py`, gives the numbers). You decide each group, from the owner's words and the
   agent message they answer:
   - **not a lesson**: the reply moved the work on and teaches nothing for later. Record it.
   - **a lesson, the first time**: say it in one sentence an agent could follow next time. When a
     file already says it, there is no proposal. Otherwise it is a proposal of the retro for the
     file that owns the step, as step 2 of "learn" says, with the lessons file as the last choice;
     a ruling too ("A ruling"). The retro edits no file for it.
   - **a lesson that came back**: the same lesson in two or more sessions or on two or more days,
     in this run's groups or in `lessons`, or one that a file already held when the owner had to
     say it again. Name the record that did not hold and why it did not reach the step: never
     read, read and buried, or contradicted by the text the step itself loads. Draft the move as a
     proposal of the retro.
3. **Record every group**, after the retro added its run (step 4 of "retro"), so that each
   proposal has its name:

   ```bash
   lem corrections record ID --decision lesson --verdict proposed \
       --target PATH --lesson "the sentence (retro of 2026-11-24 #3)"
   ```

   `--verdict` is `proposed` for a lesson that went into a proposal, with `--target` the file the
   proposal would change and the proposal's name at the end of `--lesson`; `unasked` for a group
   with no proposal (not a lesson, or a lesson a file already held, with that file as `--target`);
   `missed` when the owner said that a "not a lesson" entry was one. `accepted`, `changed` and
   `rejected` are his answer to a move a session put to him, which a retro never does. A
   `proposed` lesson is in no file yet: `lem corrections lessons` gives it with that verdict, and
   the retro never reads it as a lesson to remove.
4. **End with the counts**: groups read, lessons and how many of them came back, proposals made
   and for which files, and the filter's precision in this run: lessons over flagged entries.

The hook sees only what the owner types as a message. An answer the owner gives on a page never
reaches the queue.

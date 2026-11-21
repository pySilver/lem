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
     (`lem project path lessons`) that opens with the stage's or the skill's name (`new: ...`),
     which Lem reads before each subcommand. Never the installed skill's own file, whether it is
     a link to a clone or a plugin's copy: that file is the same for every repository that uses
     it, an edit there is live in all of them at once with no review, and a plugin's next update
     drops it. Your report says that the line is a lesson about Lem itself, so the owner can
     bring it to whoever maintains Lem;
   - how code is written here: the rule file of `.claude/rules` whose scope covers it
     (`lem project path rules`);
   - what a person of the project wants or notices: that persona's file
     (`lem project path personas`);
   - what a review should catch or stop raising: the lens, the review profile or the
     rejected-findings list (`lem project path review`). That folder is the review tool's own:
     Lem never moves, links or reshapes it, and a lesson still writes a line into a file there;
   - a decision about the product that outlives the task: a ruling, a file in the rulings folder
     (`lem project path rulings`) named as `lem project ruling-file SLUG` prints it (`name`);
   - a command shape a pattern can match: a hook or a commit check of the repository that refuses
     it and names the replacement;
   - none of these: one line in the project's lessons file (`lem project path lessons`), which the
     plan and build stages read.
3. **When the owner asked for the change, make it** and say, for each file you changed, its path,
   what changed and why, in one to three lines a file. When you found the lesson yourself, show
   the edit with the same three things and make it on the owner's "apply". No file a lesson
   changes goes unnamed, whichever folder holds it.
4. A lead commits a project file on the task's branch with the work. A session with no task's
   branch (a retro, a session of no task): there the edit of a project file is a task of its own
   (`/lem new`), so it lands through the checks like any change. Every file a lesson changes is in this repository, the review tool's
   folder included: never a file in the home directory, and no session commits in another
   repository. A retro started in one repository once committed an edit of a stage on the
   checked-out base branch of the clone the skill was linked from, with nobody's review, and the
   next push from that clone published it (2026-11-17).

A lesson about one project never goes into a skill, and the lessons file never holds what a style
guide file, a persona or a lens could hold: it is the last target, and it stays short enough to be
read whole. Every session reads it before each subcommand, so each line of it is paid for at every
step and a wrong one is carried into every task: when it grows, move a line's detail down into the
file that owns its step, or into a ruling, and leave the one sentence that points there.

## retro

`/lem retro` reads what the sessions did since the last retro: each task's decisions
(`lem decisions list SLUG`: who took each, a pick past the personas, a breaker and the owner's help on it), the
"not verified" and "outside defects" lines of each `report.md`, the reviews and the proposals
in the event log (`review` and `proposed` events: the rounds, the counts, who answered, and each
reason a request was not green; `careful.missed` events: a change the review called careful and
its plan's own call did not, with the round and the review's reason), and the owner's corrections, from the project's correction queue when it keeps one (below). It looks
for what came back:

- a correction the owner gave more than once: the record it had did not reach the step; move it
  with step 2 above, and put the move to the owner;
- a decision the owner overturned: the rule that would have decided it right, as a ruling or a
  rule line;
- a task the owner made careful after its lead called it plain, a `careful.missed` event, or a
  defect a review found in a plain task. First find which it was. A topic named it, and the lead
  read the plan wrong: the lesson is about that judgment, and it may be sharper words for the
  topic. No topic named it: propose one sentence for `flow.topics` to the owner, as a move; the
  settings change on his yes only;
- a review finding that repeats across items: a rule line or a check, so the builder meets
  it before the review does;
- a check or a step of this skill that cost time and changed nothing: propose to remove
  it, with the turns that show the cost;
- a lesson the days no longer bear out. Read each line of the project's lessons file, and each
  lesson an earlier retro recorded (`lem corrections lessons`, with the file it went to), against
  the records since it was written: the thing it names is gone, the tasks went the other way and
  nobody objected, or the owner said the opposite later. Propose its removal or its new words to
  the owner as a move, with the task that shows it. A lesson is never removed because it is old;
- a choice that climbed past the personas and held: the same question decided by the dialectic or
  the experts in two tasks or more, or one such pick that the owner kept when he read its pull
  request. The next task pays for that climb again unless the answer is where the first level
  finds it, so propose it to the owner as a ruling, in his rulings folder, with both tasks. It is
  his to approve: a pick of the experts is no ruling of his until he says so.

Where the project has naps (`stages/nap.md`), the retro also reads their waking notes,
`naps/*/waking.md` in the folder `lem project state-dir` prints, of each nap whose time, the start
of its folder's name, is after the retro before this one. A waking note is one agent's impression
after a dream, so it is a candidate and never a lesson: a thing a note names becomes a lesson only
when the tasks' records above show it too, and that lesson says which note it came from, by the
folder's name. The same holds for a lesson a note says no longer fits the days: it is a candidate
for the removal above, checked against the records like any other. A note is never put to the owner as a proposal by itself, and the dream beside it
is not read for lessons.

The owner sees only moves and removals, in one question through `ask-owner`, each with the case
in their own words. A retro that a scheduled job started, with nobody at the terminal, opens no
page: a page would wait in a session nobody sees (on 2026-11-17 one did). It writes the moves and
removals into one file, `retros/YYYY-MM-DD.json` in the folder `lem project state-dir` prints, in
the form Lem's question page takes: one question for each proposal, its prompt the move in one
line, its body the file, the change and the case, and the options approve, reject and later. Then
it ends, with its closing report. `lem project waiting` lists the file, and a bare `/lem` says "the
retro of DATE proposes N changes"; on the owner's word Lem opens the proposals on one page, as
`stages/status.md` says, and makes each move he approved. First-time lessons are recorded without a question. The retro's closing report still names every
file it changed, a first-time record included, with what changed and why.

## The correction queue

An optional part. A session that is corrected does not always record it, and a correction that
is given again is what a retro is for. So a project may keep a queue: a hook asks a small
decision model about each message the owner types, and queues the ones an agent should learn a
lesson from. The project's settings turn it on (`corrections.collect`), and `stages/init.md` says
how the owner agrees to it. `lem project show` says whether it is on. When it is off, skip this
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
   (`corrections.py` gives the numbers). You decide each group, from the owner's words and the
   agent message they answer:
   - **not a lesson**: the reply moved the work on and teaches nothing for later. Record it.
   - **a lesson, the first time**: say it in one sentence an agent could follow next time. When a
     file already says it, there is no edit. Otherwise put it in the file that owns the step, as
     step 2 of "learn" says, with the lessons file as the last choice. Nobody is asked.
   - **a lesson that came back**: the same lesson in two or more sessions or on two or more days,
     in this run's groups or in `lessons`, or one that a file already held when the owner had to
     say it again. Name the record that did not hold and why it did not reach the step: never
     read, read and buried, or contradicted by the text the step itself loads. Draft the move, and
     put it to the owner as the retro does.
3. **Record every group**, also the ones nobody was asked about:

   ```bash
   lem corrections record ID --decision lesson --verdict accepted \
       --target PATH --lesson "the sentence"
   ```

   `--verdict` is the owner's answer to a move (`accepted`, `changed`, `rejected`), `missed` when
   the owner says that a "not a lesson" entry was one, or `unasked` for a group nothing was asked
   about. `--target` is the file the lesson went to, or the one that already held it.
4. **End with the counts**: groups read, lessons and how many of them came back, edits made and
   where, and the filter's precision in this run: lessons over flagged entries.

The hook sees only what the owner types as a message. An answer the owner gives on a page never
reaches the queue.

# learn and retro

A correction holds when it changes the text an agent reads at the moment it does the step. A note
read at session start does not: one note was opened before the step it governs in 2 of 42
sessions, and the owner gave that correction again to eight sessions in two minutes (mybaze,
2026-11-12). A rule loaded at session start lost to a skill template that said otherwise.

## learn, in the session

When the owner corrects you, disagrees with an approach, or tells you something for the second
time ("again", "I told you", "we discussed"), do this in the same reply, before going on. The
owner may correct Lem or, in a task's session, its lead; whoever was corrected does it:

1. **Say the lesson in one sentence** an agent could follow next time.
2. **Find the file that owns the step**, the first that fits:
   - a stage of a skill (a page it builds, a message it sends, a command it runs): that skill's
     file, in the clone the skills are linked from;
   - how code is written here: the style guide file whose scope covers it
     (`project.py path styleguide`);
   - what a person of the project wants or notices: that persona's file
     (`project.py path personas`);
   - what a review should catch or stop raising: the lens, the review profile or the
     rejected-findings list (`project.py path review`). That folder is the review tool's own:
     Lem never moves, links or reshapes it, and a lesson still writes a line into a file there;
   - a decision about the product that outlives the task: a ruling (`project.py path rulings`);
   - a command shape a pattern can match: a hook or a commit check that refuses it and names the
     replacement;
   - none of these: one line in the project's lessons file (`project.py path lessons`), which the
     plan and build stages read.
3. **When the owner asked for the change, make it** and say, for each file you changed, its path,
   what changed and why, in one to three lines a file. When you found the lesson yourself, show
   the edit with the same three things and make it on the owner's "apply". No file a lesson
   changes goes unnamed, whichever folder holds it.
4. A lead commits a project file on the task's branch with the work. Lem has no task's branch:
   there the edit of a project file is a task of its own (`/lem new`), so it lands through the
   gate like any change. Skill files are committed in their clone and never pushed from here.

A lesson about one project never goes into a skill, and the lessons file never holds what a style
guide file, a persona or a lens could hold: it is the last target, and it stays short enough to be
read whole.

## retro

`/lem retro` reads what the sessions did since the last retro: each task's `decisions.md`, the
"not verified" and "outside defects" lines of each `report.md`, the review queue's outcomes, and
the owner's corrections, from the project's correction queue when it keeps one (below). It looks
for what came back:

- a correction the owner gave more than once: the record it had did not reach the step; move it
  with step 2 above, and put the move to the owner;
- a decision the owner overturned: the rule that would have decided it right, as a ruling or a
  style guide line;
- a task the owner made careful after its lead called it plain, or a defect a review found in a
  plain task. First find which it was. The settings named the topic or the path, and the lead
  read the plan wrong: the lesson is about that judgment, and it may be sharper words for the
  topic. No setting named it: propose one line for `flow.topics` or `flow.careful` to the owner,
  as a move; the settings change on his yes only;
- a review finding that repeats across items: a style guide line or a check, so the builder meets
  it before the review does;
- a gate, a check or a step of this skill that cost time and changed nothing: propose to remove
  it, with the turns that show the cost.

The owner sees only moves and removals, in one question through `ask-owner`, each with the case
in their own words. First-time lessons are recorded without a question. The retro's closing report still names every
file it changed, a first-time record included, with what changed and why.

## The correction queue

An optional part. A session that is corrected does not always record it, and a correction that
is given again is what a retro is for. So a project may keep a queue: a hook asks a small
decision model about each message the owner types, and queues the ones an agent should learn a
lesson from. The project's settings turn it on (`corrections.collect`), and `stages/init.md` says
how the owner agrees to it. `project.py show` says whether it is on. When it is off, skip this
section.

```bash
python3 SKILL_DIR/scripts/corrections.py list      # unreviewed groups, most sessions first
python3 SKILL_DIR/scripts/corrections.py show ID   # one group in full
python3 SKILL_DIR/scripts/corrections.py lessons   # what earlier retros recorded
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
   python3 SKILL_DIR/scripts/corrections.py record ID --decision lesson --verdict accepted \
       --target PATH --lesson "the sentence"
   ```

   `--verdict` is the owner's answer to a move (`accepted`, `changed`, `rejected`), `missed` when
   the owner says that a "not a lesson" entry was one, or `unasked` for a group nothing was asked
   about. `--target` is the file the lesson went to, or the one that already held it.
4. **End with the counts**: groups read, lessons and how many of them came back, edits made and
   where, and the filter's precision in this run: lessons over flagged entries.

The hook sees only what the owner types as a message. An answer the owner gives on a page never
reaches the queue.

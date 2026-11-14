# learn and retro

A correction holds when it changes the text an agent reads at the moment it does the step. A note
read at session start does not: one note was opened before the step it governs in 2 of 42
sessions, and the owner gave that correction again to eight sessions in two minutes (mybaze,
2026-11-12). A rule loaded at session start lost to a skill template that said otherwise.

## learn, in the session

When the owner corrects you, disagrees with an approach, or tells you something for the second
time ("again", "I told you", "we discussed"), do this in the same reply, before going on:

1. **Say the lesson in one sentence** an agent could follow next time.
2. **Find the file that owns the step**, the first that fits:
   - a stage of a skill (a page it builds, a message it sends, a command it runs): that skill's
     file, in the clone the skills are linked from;
   - how code is written here: the style guide file whose scope covers it
     (`project.py path styleguide`);
   - what a person of the project wants or notices: that persona's file
     (`project.py path personas`);
   - what a review should catch or stop raising: the lens or the rejected-findings list
     (`project.py path review`);
   - a decision about the product that outlives the task: a ruling (`project.py path rulings`);
   - a command shape a pattern can match: a hook or a commit check that refuses it and names the
     replacement;
   - none of these: one line in the project's lessons file (`project.py path lessons`), which the
     plan and build stages read.
3. **When the owner asked for the change, make it** and say what changed in one to three lines.
   When you found the lesson yourself, show the edit and make it on the owner's "apply".
4. Project files are committed on the task's branch with the work. Skill files are committed in
   their clone and never pushed from here.

A lesson about one project never goes into a skill, and the lessons file never holds what a style
guide file, a persona or a lens could hold: it is the last target, and it stays short enough to be
read whole.

## retro

`/task retro` reads what the sessions did since the last retro: each task's `decisions.md`, the
reports' "not verified" and "outside defects" lines, the review queue's outcomes, and the owner's
corrections where the project records them. It looks for what came back:

- a correction the owner gave more than once: the record it had did not reach the step; move it
  with step 2 above, and put the move to the owner;
- a decision the owner overturned: the rule that would have decided it right, as a ruling or a
  style guide line;
- a review finding that repeats across items: a style guide line or a check, so the builder meets
  it before the review does;
- a gate, a check or a step of this skill that cost time and changed nothing: propose to remove
  it, with the turns that show the cost.

The owner sees only moves and removals, on one page, each with the case in their own words.
First-time lessons are recorded without a page.

# plan

A plan here is short and written by whoever builds. It exists so the builder has thought before
typing and so a reviewer can tell what was meant; it is not argued line by line before the build.

1. **Write the plan** as one file in the settings' `plans` path, named `YYYYMMDD-<slug>.md`, and
   commit it as the branch's first commit:
   - the outcome and the "done when" from `task.md`;
   - what changes for a person, as one short run in numbered steps, when a person observes a
     change; "no person observes a change" otherwise;
   - the tasks, three to seven, each an outcome a reviewer can check alone, with the files it
     expects to touch;
   - the decisions the plan takes, each with the answer it assumes and what the answer rests on;
   - what it will not verify, and why.
   Before writing, read the style guide files whose scope covers the files the plan touches
   (`project.py path styleguide`; a file's frontmatter says its paths) and the project's lessons
   (`project.py path lessons`).
2. **Is the task careful?** Run `project.py careful` over the files the plan names. The task is
   careful when a file matches, and also when the plan starts a pattern other code will copy (a
   first service layer, a first use of a library, a new kind of test).
3. **A careful plan gets a second opinion before any code.** `second-opinion` reads the plan
   against the code, read-only, in a fresh context, and replies with the design failures it can
   show with a cite. Fix the plan for each one that holds. One such read took nine minutes and
   found three design failures before any code (convertiser-server, 2026-11-14). A plan that is
   not careful skips this.
4. **A held decision goes to the owner now, the others do not.** For each decision of the plan:
   a ruling, a test or a probe answers it → quote that. It is cheap to undo → take it and log it.
   It turns on a claim that can be argued both ways ("this will not scale", "nobody uses that")
   → the `dialectic` skill settles the claim first. Its options each cost a person something and
   nothing answers it → the `gate` skill, then the `panel` skill with the project's cast, then the
   owner. Ask all
   held decisions of the plan in one go, and build the tasks that do not depend on them meanwhile.
   The `panel` skill writes the card the owner sees and says how its page opens. Add the two
   things a card does not carry: above it, the run `SKILL.md` asks for, ending badly, and
   whether it was reproduced or derived; and one line on why it became
   possible and how far the same cause reaches. When the owner wants to read or mark up the
   plan itself, open it with the settings' `tools.annotate`.
5. **Go on to `build`.** Write a block in `state.md`.

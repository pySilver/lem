# plan

The lead's first stage. A plan here is short and written by whoever builds. It exists so the
builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build.

1. **Write the plan** as one file in the settings' `plans` path, named `YYYYMMDD-<slug>.md`, and
   commit it as the branch's first commit:
   - the outcome and the "done when" from `task.md`, each "done when" line sharpened to a command
     or a look at the product now that you have read the code;
   - what changes for a person, as one short run in numbered steps, when a person observes a
     change; "no person observes a change" otherwise;
   - the tasks, one to seven, each an outcome a reviewer can check alone and one builder can
     finish in a context of its own, with the files it expects to touch;
   - the decisions the plan takes, each with the answer it assumes and what the answer rests on;
   - what it will not verify, and why.
   Before writing, read the style guide files whose scope covers the files the plan touches
   (`project.py path styleguide`; a file's frontmatter says its paths) and the project's lessons
   (`project.py path lessons`).
   When the branch already holds a plan (a night draft, a builder that stopped at the plan), do
   not write another: read it against the code as it is now, and commit a fix for what the code
   has outgrown.
2. **Is the task careful?** Run `project.py careful` over the files the plan names. The task is
   careful when a file matches, and also when the plan starts a pattern other code will copy (a
   first service layer, a first use of a library, a new kind of test). An outcome that needs more
   than seven tasks is two asks: say so in the report, and plan the first.
3. **A builder does not lead a careful task.** When your brief says `lead: builder` and step 2
   says careful: write `report.md` with the pattern or the reason that says so; write the state
   `planned` with the line `needs a session: careful`; and stop. Lem opens a session, and its lead
   starts from your plan. When your brief says `stop after the plan: yes`, stop the same way with
   the line `the owner reads the plan`.
4. **A careful plan gets a second opinion before any code.** This is the session's step, and it
   comes before step 5 lets any task be built.
   `second-opinion` reads the plan against the code, read-only, in a fresh context, and replies
   with the design failures it can show with a cite. Fix the plan for each one that holds. One
   such read took nine minutes and found three design failures before any code
   (convertiser-server, 2026-11-14). A plan that is not careful skips this.
5. **A held decision goes to the owner, the others do not.** For each decision of the plan: a
   ruling, a test or a probe answers it → quote that. It is cheap to undo → take it and write it
   in `decisions.md`. It turns on a claim that can be argued both ways ("this will not scale",
   "nobody uses that") → the `lem-dialectic` skill settles the claim first. Its options each cost a
   person something and nothing answers it → it is held, and it is not yours to ask. Write it in
   `report.md` under "held", so that Lem can ask it without reading the code:
   - one concrete case in numbered steps that ends badly, with real names and values and where
     each step was read, and whether you reproduced it or derived it;
   - one line on why the case became possible and how far the same cause reaches;
   - the options, each as what a person would see and what it costs, and what you would choose.
   Then build the tasks that do not depend on a held decision. Write the state `held` and stop
   only when every task that is left depends on one. A builder whose plan is careful has stopped
   at step 3 before this, and the session that takes the plan over does step 4 first.
6. **Go on to `build`.** Write the state `building` with the line `plan committed, N tasks`.

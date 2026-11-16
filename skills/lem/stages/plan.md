# plan

The lead's first stage. A plan here is short and written by whoever builds. It exists so the
builder has thought before typing and so a reviewer can tell what was meant; it is not argued line
by line before the build.

1. **Write the plan** as one file in the settings' `plans` path, named `YYYYMMDD-<slug>.md`, and
   commit it as the branch's first commit. It opens with the stories, because they are the
   owner's document: he reads them and not the rest of the plan, and they become the tests.
   - `## Stories`, in the form `python3 SKILL_DIR/scripts/stories.py --help` shows. A story is
     one business rule of the request in plain language with one concrete example, with real
     names and values: what a person of the project would see, never how the code does it. Take
     them from the outcome and the "done when" of `task.md`, now that you have read the code. A
     rule you cannot write without guessing what the owner wants is not yours to guess: it is a
     held decision (step 5), and Lem asks him;
   - the first line of that section is your call, `Kind: feature` or `Kind: correction`, with
     the reason after `because`. A correction is a request that yields one story and is not
     careful (step 2): its story is the owner's own sentence made exact. Everything else is a
     feature. The owner may overrule the call, as he may the careful one;
   - run `python3 SKILL_DIR/scripts/stories.py record SLUG`: it refuses a section that does not
     have the form, and it puts the stories where the board and Lem's status show them;
   - `## Tasks`: a numbered list of one to seven tasks, each an outcome a reviewer can check
     alone and one builder can finish in a context of its own, with the stories it serves and
     the files it expects to touch. The landing counts the numbered lines under that heading:
     a plan of more than three gets a review round at the least, and a plan with no such list
     is refused there;
   - the decisions the plan takes, each with the answer it assumes and what the answer rests on;
   - what it will not verify, and why;
   - `## The bar`, only when the change has to lower it (a lint or type suppression, a skipped
     or deleted test, fewer assertions in a test): one line for each such file, `- PATH: REASON`.
     The landing refuses a lowered bar with no reason, and with one the pull request is not
     green: the owner reads that line himself. So lower it only where the mark is right.
   Before writing, read the style guide files that cover the files the plan touches and the
   project's lessons (`project.py path lessons`). `python3 SKILL_DIR/scripts/project.py rules
   FILE ...` prints those style guide files, the ones with no scope of their own too: do not
   match a file's `paths:` by eye.
   When the branch already holds a plan (a night draft, a builder that stopped at the plan), do
   not write another: read it against the code as it is now, and commit a fix for what the code
   has outgrown.
2. **Is the task careful?** Three tests, and one yes is enough:
   - *a path*: `project.py careful` over the files the plan names. A match is a yes that no
     judgment of yours overturns.
   - *a topic*: the project's danger topics (`flow.topics` in `project.py show`), each a
     sentence of the owner's about what must not go wrong here. Read the plan against each one:
     does a task change how that thing behaves, or could a defect in a task reach it? No code
     matches a topic, and no file name settles it: a price is computed in more places than
     `billing/`. This is your judgment, and a person can overlook a danger that you see in the
     code, so say what you see.
   - *a pattern*: the plan starts something other code will copy (a first service layer, a
     first use of a library, a new kind of test).
   Write the call into the plan as one line under its title, before `## Stories` (a line that
   is no story is refused inside that section), `careful: yes` or `careful: no`, with the one
   sentence of why: the path, the topic in the owner's words, the pattern, or what you checked
   to say that none is touched. The same line goes into your next state block, where the owner
   reads it on the board while the task builds, and into the report.
   An outcome that needs more than seven tasks is two asks: say so in the report, and plan the
   first.
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
   (convertiser-server, 2026-11-14). In another repository a plan round before any code found at
   least one major finding in 7 of 9 plans whose records tell majors from minors, and the largest
   found 19 (mybaze, 2026-09-25 to 2026-11-03, counted by one reader from that project's notes).
   A plan that is not careful skips this read, and that is what the skip can cost.
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

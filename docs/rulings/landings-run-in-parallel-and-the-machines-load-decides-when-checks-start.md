---
ruled: 2026-11-20
area: The review, the pull request and the merge
---

# Landings run in parallel, and the machine's load decides when checks start

His rulings of 2026-11-20 and 2026-11-21, while his interview redesigned how a task runs and the
board became a served app; a quote is his words. His answers Q7 to Q11 and notes P1 to P9 are in
`.lem/state/tasks/one-lem-parallel-landings/`, which git ignores. Where a note replaces an earlier
ruling, this is the ruling now.

The first three tasks of the redesign, in the order he agreed to (Q9, "Yes I agree"):

**Landings run in parallel, and the machine's load decides when checks start**: "tests should run
in parallel", under Umputun's load-average rule, and "on macbook I want to be able to use laptop
comfortable, on my powerful mac mini: I can hummer it" (P7). This replaces his "yes" of 2026-11-19
to one landing at a time (criterion 6 of `landing-in-the-background`), and his count of check runs
of the same morning. The form is the session's: `lem land start` takes any number of tasks; the
checks start only below `[load] start` of `machine.toml` (`lem project load --start N`), two runs
start at least 60 s apart (a guess), and with no number there is no gate; merges go one at a time
under `merge.lock`. At a start of 1 in his first trial: "We stuck, I think LA will never get that
low."

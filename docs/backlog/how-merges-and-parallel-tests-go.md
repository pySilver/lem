---
worth: maybe
where: skills/lem/stages/land.md
added: 2026-11-19
---
# how merges happen, and whether a project runs its tests in parallel

The owner: "explore how merges happening and whether parallel tests are running usually in
project" (2026-11-19). An open question for research, before any change.

What one day in Lem's own repository showed (2026-11-19):

- One task is in `landing` at a time, and the full suite runs under one lock (`checks.serial`),
  so the landing of status-boards-steady-look waited while another task's checks ran.
- `bash tests/all.sh` runs its suites at the same time. `tests/lem-picker.sh` passed alone on the
  branch and on `main`, and failed inside `all.sh`, because a minute boundary fell in its slower
  setup. A task for that test landed first (#2) and held the landing for about an hour.
- Pull requests #3 and #4 were open together, and #4 merged first. The forge did not call #3
  conflicting afterwards; Lem brings onto the base only a pull request the forge calls
  conflicting.

Questions to answer with sources (what teams that use GitHub pull requests do, and what the test
runners of common stacks do by default):

1. How do teams merge several open pull requests: one at a time with a rebase and a new test run,
   a merge queue (GitHub's merge queue, a bot), or as they are?
2. Do projects usually run their test suites in parallel (pytest-xdist, Jest workers, Go's
   packages), and do they keep the slow or shared-resource tests serial?
3. What does that mean for Lem's landing line, its one lock for `checks.serial`, and a test that
   passes alone and fails in a parallel run?

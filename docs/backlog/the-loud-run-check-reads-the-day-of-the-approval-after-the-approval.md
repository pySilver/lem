---
worth: later
where: tests/lem-land-review.sh
added: 2026-11-22
---
# The loud-run check reads the day of the approval after the approval

The check of `tests/lem-land-review.sh` that says a task is not green when something of the owner's
was decided without him runs `lcriteria approve loud-run --alone` first, then five landing steps
(`start`, `base`, the polish, `checks`, `read`, `propose`), and only then `day=$(date -u +%Y-%m-%d)`.
It expects the pull request's text to say "they were approved on $day". A run whose approval falls
on 2026-11-22 at 23:59:59 UTC and whose `date -u` call falls after midnight expects "approved on
2026-11-23" and finds "approved on 2026-11-22", so the check fails with nothing wrong in Lem. Taking
the day just before the approval, and once more after it, and accepting either (as `day_from` and
`day_to` do in `tests/lem-land-backlog.sh`), would close it.

Seen outside the change by the builder of task prune-test-minute-race (2026-11-22); the base commit has it.

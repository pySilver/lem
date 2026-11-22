---
worth: later
where: skills/lem/prompts/review.md
added: 2026-11-22
---
# The review prompt asks for left-out profiles that the full set refuses

Step 3 of `prompts/review.md` says "Write one reason for each profile you run and each you leave
out", and step 8 asks for `left_out` with a `why` each, with no exception for `full`. `lem land read
--record` refuses any `left_out` when the kind is `full` ("the project's full set leaves no profile
out: a profile may be added to it, never dropped", `land.py`, the check `if kind == "full" and
left_out`). In github-issues-tracker's landing (2026-11-22) the review agent ran the profile
`comprehensive` as the full set and listed the other rosters (`focused`, `final`, `claude-only`,
`codex-only`, `grill-me`, `expert`, `triage`) under `left_out`, as the prompt asks; the record was
refused, and the agent had to be resumed to empty `left_out` and move the reasons into its
`review-N.md`. That costs a review agent's resume on every careful landing.

One of the two texts moves: the prompt says that a `full` record has `left_out: []` and that the
other rosters' reasons go in `review-N.md`, or the script takes a `left_out` of profiles that are not
part of the full set. The prompt's line is the cheaper change; a case in the land suite that records
a `full` review with `left_out: []` already holds the script's side.

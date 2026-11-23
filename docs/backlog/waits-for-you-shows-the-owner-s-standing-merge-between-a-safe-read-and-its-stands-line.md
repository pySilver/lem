---
worth: later
where: skills/lem/scripts/lem_board_model.py:merge_wait
added: 2026-11-23
---
# Waits for you shows the owner's standing merge between a safe read and its stands line

The owner presses Merge on pull request 60, of tip `faac6eb3b`, and Lem refuses it because `main`
moved to `d48c6a9bd` (`merge.refused`, `by: owner`, `from: lem`, `kind: base`). A fresh merge
agent reads what moved, and its `merge-review` run logs two lines: first `merge.review` with
`base_call: safe`, `verdict: call` and `calls: true` (a careful request), then `merge.stands` for
`faac6eb3b`. On #60 both carry 10:41:22. Between the two lines, `fold` clears the refusal
(`answers_refusal`) and `merge_wait` sees a review of the tip that calls the owner and no
`merge.stands` yet, so it says "owner". The task is then `for_owner`, in the lane "you", and
`waits_of` gives it a "review" row and a "merge" row of "Waits for you". The merge row has no
button, since `acts_of` reads `owner_stands`, which the read's mark (`Task.stood`) already holds.
The window is one `project.py log` call long, so a board refresh or the Inbox's look rarely meets
it; when one does, the owner sees his own standing merge ask for him again. `merge_wait` could
read `Task.stood` as it reads `merge.stands` and say "merges" there; the unit case
`tests.unit.test_board_model.MovedBase.test_his_merge_stands_from_the_refusal_through_the_servers_merge_and_its_sentence_follows_the_span`
asserts "owner" for that cut today, so the fix changes that assertion too.

Seen outside the change by the builder of task standing-merge-shows-as-waiting (2026-11-23); the
gap is in `merge_wait` on the base commit, and the change made the merge row there one with no button.

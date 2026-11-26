# Notes of the step `journeys`

## 1. Rows that the journeys of this step prove, for their owners

Each row below has no fate in its owner's file: it came to that step by a move after the step was
done. The journey named proves it as written, or as the note says. The owner writes the fate.

| Owner | Row | Proof | Note |
| --- | --- | --- | --- |
| `task` | `check:tests/lem-decisions.sh:a-dropped-task-stays-dropped-and-its-resume-4cb48ada68901d88` | `journeys.test_park_drop.test_a_dropped_task_with_a_breaker_goes_on_in_a_new_task_from_its_commits` | kept |
| `task` | `check:tests/lem-decisions.sh:a-parked-task-gets-no-lead-takes-no-late-sta-a55a45734936af39` | `journeys.test_park_drop.test_a_task_that_waits_for_the_owner_is_parked_and_comes_back_as_it_was` | with `test_a_task_an_agent_works_on_is_not_parked_and_a_planned_one_is` and the breaker's park and resume in `test_a_dropped_task_with_a_breaker_goes_on_in_a_new_task_from_its_commits`; his help on the breaker is `unit.criteria.test_decisions.test_his_help_on_a_breaker_is_the_owners_and_settles_it_once` |
| `task` | `check:tests/lem-decisions.sh:a-task-two-releases-back-stops-at-its-first-417a4d8879a707ca` | `journeys.test_park_drop.test_a_task_the_release_stop_held_is_dropped_and_goes_on_as_a_new_request` | kept |
| `task` | `check:tests/lem-decisions.sh:a-lead-whose-task-needs-another-task-s-resul-0f3ddd6189435167` | `journeys.test_park_drop.test_a_queued_task_starts_when_the_one_before_lands_and_on_his_word_after_a_drop` | "a task with its landing is never queued" is not in the journey |
| `task` | `check:tests/lem-decisions.sh:his-start-it-for-a-task-queued-behind-a-drop-c3c61905db4d491a` | `journeys.test_park_drop.test_a_queued_task_starts_when_the_one_before_lands_and_on_his_word_after_a_drop` | his words, with a double quote and an apostrophe, are the journal's line |
| `task` | `check:tests/lem-settings.sh:a-landed-task-keeps-its-issue-for-good-a-new-56ac93e9239b2431` | `journeys.test_hard_paths.test_a_ticket_step_owed_at_the_end_is_paid_after_it_and_the_ticket_stays_the_tasks` | with a Linear ticket; the GitHub issue is the same claim |
| `task` | `check:tests/lem-settings.sh:ticket-step-writes-each-thing-lem-did-to-a-t-b5983e1972615b93` | `journeys.test_hard_paths.test_a_ticket_step_owed_at_the_end_is_paid_after_it_and_the_ticket_stays_the_tasks` | once, and a second time refused; an unknown step is Click's exit 2 |
| `land-propose` | `check:tests/lem-land-shop.sh:a-plan-of-four-tasks-with-no-plan-talk-is-no-7299403f55c58fb9` | `journeys.test_standard_track.test_a_plan_of_four_tasks_is_proposed_only_after_its_plan_talk` | the talk's form is `task talked`'s (`unit.task`) |
| `land-propose` | `check:tests/lem-land-shop.sh:after-its-plan-talk-a-plan-of-four-tasks-is-93690b8936d896f6` | `journeys.test_standard_track.test_a_plan_of_four_tasks_is_proposed_only_after_its_plan_talk` | kept |
| `land-propose` | `check:tests/lem-land-shop.sh:the-pull-request-is-opened-on-github-the-tas-3eba9a0191bd2909` | `journeys.test_standard_track.test_a_standard_task_goes_from_its_request_to_a_cleaned_merge` | kept |
| `land-propose` | `check:tests/lem-land-backlog.sh:a-task-started-from-a-backlog-item-stops-at-6071fd102835c6d6` | `journeys.test_night.test_a_night_task_of_an_item_runs_without_the_owner_to_a_request_he_merges` | kept |
| `land-propose` | `check:tests/lem-land-review.sh:a-task-that-ran-without-the-owner-is-not-gre-8f2051c7e5ab37b5` | `journeys.test_owner.test_criteria_approved_while_he_was_away_make_the_request_not_green_for_his_merge` | the criteria's line only; the experts' and the dialectic's lines are not in the journey |
| `criteria` | `check:tests/lem-land-local.sh:without-the-owner-the-criteria-are-approved-7d6e6a9261f90d06` | `journeys.test_owner.test_criteria_approved_while_he_was_away_make_the_request_not_green_for_his_merge` | with the night's `--alone` in `journeys.test_night.test_a_night_task_of_an_item_runs_without_the_owner_to_a_request_he_merges`; the fast track of his own request is refused `his-request` |

## 2. Path rows whose proof is a unit case, and a journey now proves the whole path

| Owner | Row | Journey |
| --- | --- | --- |
| `land-checks` | `path:red-base` | `journeys.test_hard_paths.test_a_red_base_waits_for_its_repair_task_and_lands_after_it`: the red run, the repair task, `lem task red-base`, the repair's landing, `ready` again and the landing. Its fate's note says that no command sets the hold; `lem task red-base` does now |
| `task` | `path:drop-during-a-step` | `journeys.test_park_drop.test_a_drop_during_the_checks_stops_them_and_takes_the_step_lock`, `test_a_drop_waits_for_another_step_and_drops_after_it`, `test_a_merge_on_the_forge_while_the_drop_waits_defeats_it_and_the_task_lands` |
| `task` | `path:ticket-after-the-end` | `journeys.test_hard_paths.test_a_ticket_step_owed_at_the_end_is_paid_after_it_and_the_ticket_stays_the_tasks` |

## 3. For `core`: the journeys level on four workers

The design's aim for the journeys level is 4 minutes. On 2026-11-25 the level took 1,155 s for
277 cases in one process, at a load average of 9 to 20, while two other worktrees ran their own
journeys. The 251 cases before this step took 1,080 s the same evening. The 26 cases of this step
took 100 s alone, at a load average of 9. With `tests/levels.py`'s `parallel` giving the journeys
level the unit level's four xdist workers (a probe: the line changed, one run, the line put
back), all 277 cases passed in 368 s, at a load average of 14 to 15. The request: let `parallel`
give the journeys level the same workers. A journey has its own home, folder and ports already
(`tests/journeys/conftest.py`).

## 4. For `ledger`: a proof that names a parametrized test

`check.py` takes a proof only by its exact name, so a proof that names a parametrized test
without its case is "not in the results" though each case passed. This step pointed four such
proofs at their first case (in `fates/addons-flow.tsv`, `fates/land-review.tsv` twice and
`fates/board-duties.tsv`). A fix at the source: `Results.why_not` takes a name `NAME` as passed
when the results hold one or more `NAME[CASE]` lines and each of them passed.

## 5. Rows of kinds path, check, act and seam with no fate, in steps that are done

The check of every step (`tests/ledger/check.py`, 2026-11-25) gives 182 such rows with no fate
in their owner's file, all moved to it after it was done: `task` 50, `land-base` 33,
`land-propose` 28, `criteria` 18, `sessions` 18, `board-pages` 9, `board-views` 7,
`board-duties` 7, `land-review` 6, `addons-outside` 2, `board-acts` 2, `board-service` 1,
`owner` 1. Part 1 names a proof for 13 of them. With the other kinds, 448 rows of done steps
have no fate. Each line below is the owner and the row.

```text
addons-outside	check:tests/lem-board-act.sh:while-the-owner-is-away-the-server-sends-a-b-c0a9c6432b518d99
addons-outside	check:tests/lem-serve.sh:while-the-owner-is-away-the-phone-s-page-of-b79df97f5c52e559
board-acts	check:tests/lem-serve.sh:the-board-jumps-only-to-a-task-s-own-session-3baa19312946d35e
board-acts	check:tests/lem-serve.sh:the-owner-s-merge-from-a-task-s-panel-on-a-p-2f44b1f2d159e5fa
board-duties	check:tests/lem-board-act.sh:a-merge-that-meets-the-base-another-merge-mo-ba46911d673fc366
board-duties	check:tests/lem-board-act.sh:a-merge-that-meets-the-base-another-merge-mo-d615c678e8d8b8f5
board-duties	check:tests/lem-board-act.sh:after-github-closed-a-pull-request-with-no-m-2f1f1f8af22836a0
board-duties	check:tests/lem-board-act.sh:after-github-merged-a-pull-request-the-serve-af2cd62f23f46b58
board-duties	check:tests/lem-board-act.sh:after-the-merge-agent-s-verdict-merge-the-se-39991341011e91ab
board-duties	check:tests/lem-board-act.sh:two-merges-from-the-server-of-one-repository-7af5aaa48df5b8ca
board-duties	check:tests/lem-serve.sh:a-task-that-ended-long-ago-keeps-only-its-sm-e64f3fcd4b91ee93
board-pages	check:tests/lem-serve.sh:a-back-gesture-from-a-task-s-criteria-tab-to-bc77fd75f3553a05
board-pages	check:tests/lem-serve.sh:a-document-with-a-chart-names-the-diagram-li-a25219f292c57409
board-pages	check:tests/lem-serve.sh:a-phone-page-whose-network-stops-forwarding-bd7f00da021e9d83
board-pages	check:tests/lem-serve.sh:a-refresh-of-the-page-keeps-the-words-the-ow-cee4c343dbf6c614
board-pages	check:tests/lem-serve.sh:a-refresh-soon-after-a-finger-opened-a-task-24f477b4a59c4a23
board-pages	check:tests/lem-serve.sh:a-task-s-overview-and-each-of-its-tabs-and-e-af2e3a21d12b6f83
board-pages	check:tests/lem-serve.sh:the-backlog-s-filter-comes-from-the-address-1750c50636461adc
board-pages	check:tests/lem-serve.sh:the-switcher-names-the-workspace-whole-howev-c0cd55c93da547ac
board-pages	check:tests/lem-serve.sh:the-tasks-view-and-activity-draw-the-search-e106e4e423458336
board-service	check:tests/lem-board-act.sh:a-page-of-the-board-carries-referrer-policy-49b6c38895b08022
board-views	act:Task panel/park
board-views	check:tests/lem-board-act.sh:on-this-mac-a-row-of-waits-for-you-has-the-o-e86daedf052bb2d8
board-views	check:tests/lem-serve.sh:a-breaker-is-one-row-of-waits-for-you-its-do-0fac0d6a6b5e2d8a
board-views	check:tests/lem-serve.sh:a-proposal-that-is-not-green-lists-each-reas-4002680f34c6c91a
board-views	check:tests/lem-serve.sh:a-task-queued-by-his-order-after-a-task-he-d-d74fe1f761fff33e
board-views	check:tests/lem-serve.sh:the-backlog-view-shows-the-reviewer-s-items-293461c2545c863d
board-views	check:tests/lem-serve.sh:the-kanban-puts-each-task-in-the-column-of-w-d00b49669630e52f
criteria	check:tests/lem-land-local.sh:a-plan-that-says-size-small-is-refused-by-th-d55a804a9fae20d2
criteria	check:tests/lem-land-local.sh:a-read-by-the-lead-with-one-model-family-in-44f308ca5d3ce791
criteria	check:tests/lem-land-local.sh:a-read-freezes-only-the-first-contract-of-a-2f9f32ad22761560
criteria	check:tests/lem-land-local.sh:for-a-full-change-from-a-complete-request-hi-220251e845454336
criteria	check:tests/lem-land-local.sh:without-the-owner-the-criteria-are-approved-7d6e6a9261f90d06
criteria	check:tests/lem-machine.sh:the-builder-s-definition-names-its-model-and-596589b79561e30a
criteria	check:tests/lem-settings.sh:a-change-of-the-criteria-from-the-owner-s-no-a0d1f764b606c526
criteria	check:tests/lem-settings.sh:a-criterion-the-plan-adds-after-the-approved-0979d516640d165f
criteria	check:tests/lem-settings.sh:a-plan-whose-criteria-are-not-the-approved-o-b01cb394e16d66dd
criteria	check:tests/lem-settings.sh:a-plan-whose-criteria-are-the-approved-ones-add0f31f4f471ea5
criteria	check:tests/lem-settings.sh:a-plan-with-no-criteria-section-no-size-a-sm-19cf17b5e4c74483
criteria	check:tests/lem-settings.sh:an-answered-task-has-no-breaker-that-waits-p-9620d670fab184da
criteria	check:tests/lem-settings.sh:an-approval-checks-and-writes-under-the-task-c2f94642230522fa
criteria	check:tests/lem-settings.sh:an-approval-has-a-number-of-its-own-his-appr-dd539e414f6b23ae
criteria	check:tests/lem-settings.sh:approve-keeps-the-criteria-the-owner-approve-1cd7bc7c03e33282
criteria	check:tests/lem-settings.sh:his-next-approval-starts-the-criterion-chang-a3174f1f820d55ba
criteria	check:tests/lem-settings.sh:lem-s-approval-of-a-small-change-in-his-name-813d628dcbb18b02
criteria	check:tests/lem-settings.sh:the-criteria-are-read-from-the-top-of-the-ta-e8f41e9986a5e6b5
land-base	check:tests/lem-land-backlog.sh:a-new-item-in-the-backlog-folder-after-a-rev-8517d3761ed62042
land-base	check:tests/lem-land-github.sh:a-careful-change-after-a-conflict-the-read-o-ad956493606a706c
land-base	check:tests/lem-land-github.sh:a-careful-change-keeps-its-review-through-a-8ece881b59db8e48
land-base	check:tests/lem-land-github.sh:a-conflict-after-a-merge-base-stops-on-the-f-f4b7e614d6d47e26
land-base	check:tests/lem-land-github.sh:a-pull-request-a-commit-on-the-base-made-con-3b8f188ae63e3a9f
land-base	check:tests/lem-land-github.sh:a-teammate-s-commit-on-the-task-s-branch-sto-8207ed77d85d6bdb
land-base	check:tests/lem-land-github.sh:after-a-merge-an-open-task-with-no-conflict-9ab9e1e1b3bd03e1
land-base	check:tests/lem-land-review.sh:a-change-of-one-space-or-the-same-edit-in-an-ff9aac3f54572925
land-base	check:tests/lem-land-review.sh:the-owner-s-careful-on-a-task-whose-pull-req-44ad2840b1b93d22
land-base	check:tests/lem-land-shop.sh:a-base-run-again-after-a-propose-cut-off-aft-1c02b7df412e7352
land-base	check:tests/lem-land-shop.sh:a-base-that-moved-back-under-a-tip-a-rebase-700308f2fb6c6fdf
land-base	check:tests/lem-land-shop.sh:a-builder-s-rebase-that-stops-on-a-later-com-4269dd6551a12ff6
land-base	check:tests/lem-land-shop.sh:a-builder-who-resolves-the-conflict-with-the-15307ac9bd78fb88
land-base	check:tests/lem-land-shop.sh:a-commit-added-after-the-proposal-stays-on-t-f2938fe399e3b4ca
land-base	check:tests/lem-land-shop.sh:a-commit-after-the-rebase-that-follows-a-red-1f51da2d49e488f3
land-base	check:tests/lem-land-shop.sh:a-conflict-on-the-rebase-after-a-red-base-is-c879b7f9884d255b
land-base	check:tests/lem-land-shop.sh:a-conflict-with-the-base-names-its-files-and-9976014b4497686f
land-base	check:tests/lem-land-shop.sh:a-first-task-that-brings-the-gate-on-its-own-f734d653fef7d01d
land-base	check:tests/lem-land-shop.sh:a-project-with-no-gate-command-lands-nothing-ad4cdca96c61e197
land-base	check:tests/lem-land-shop.sh:a-rebase-that-changes-nothing-of-the-change-16900f7b23124240
land-base	check:tests/lem-land-shop.sh:a-resolution-whose-changed-line-and-whose-co-75f7aab64ebb9f01
land-base	check:tests/lem-land-shop.sh:a-second-rebase-after-a-red-base-starts-agai-cbe8caaba21c5dbe
land-base	check:tests/lem-land-shop.sh:an-open-task-takes-the-landing-line-again-an-67e9e83709e254b6
land-base	check:tests/lem-land-shop.sh:base-on-a-git-whose-range-diff-takes-no-path-09805d965eec0f61
land-base	check:tests/lem-land-shop.sh:base-rebases-onto-the-remote-s-base-branch-a-2c126ed5976bd27e
land-base	check:tests/lem-land-shop.sh:base-run-twice-with-no-move-of-the-base-in-o-c8ab8bb9ba3a97a3
land-base	check:tests/lem-land-shop.sh:base-runs-the-plain-rebase-and-carries-the-r-1c055e2144a0e1dc
land-base	check:tests/lem-land-shop.sh:no-step-runs-on-a-task-that-did-not-take-the-fc286ce6eba152ff
land-base	check:tests/lem-land-shop.sh:no-step-runs-toward-a-branch-the-settings-re-8ad11e8411b57845
land-base	check:tests/lem-land-shop.sh:start-counts-an-open-task-s-new-landing-befo-3e3a4c41e105c4b4
land-base	check:tests/lem-land-shop.sh:start-puts-a-task-in-landing-and-a-second-ta-38e7b5b96b7345b6
land-base	check:tests/lem-settings.sh:a-landing-record-that-is-not-json-or-not-an-bdbae82b5846d046
land-base	check:tests/lem-settings.sh:may-land-refuses-a-protected-branch-any-bran-4c64691ae3d28039
land-propose	check:tests/lem-land-backlog.sh:a-line-the-session-wrote-by-hand-under-seen-b16e5ff7cc38a7f9
land-propose	check:tests/lem-land-backlog.sh:a-repository-whose-team-settings-say-finding-0a8efbfdd7dac6fe
land-propose	check:tests/lem-land-backlog.sh:a-task-started-from-a-backlog-item-stops-at-6071fd102835c6d6
land-propose	check:tests/lem-land-backlog.sh:an-item-that-was-on-the-branch-before-the-re-b394e80f4ad2e05a
land-propose	check:tests/lem-land-backlog.sh:jev-reads-each-finding-called-under-the-bar-6c26b4f18684b4ff
land-propose	check:tests/lem-land-backlog.sh:two-rounds-that-saw-defects-outside-the-chan-2dbe0a5afd753102
land-propose	check:tests/lem-land-github.sh:an-open-task-whose-last-review-left-a-must-f-0dead4e126644e05
land-propose	check:tests/lem-land-guards.sh:a-task-branch-the-owner-protected-after-its-36360647d694c7c1
land-propose	check:tests/lem-land-guards.sh:propose-refuses-notes-that-are-no-file-and-a-767052da2cb01f3e
land-propose	check:tests/lem-land-review.sh:a-branch-that-commits-the-machine-s-own-sett-35ce6111863dc4fc
land-propose	check:tests/lem-land-review.sh:a-branch-that-edits-the-flow-table-of-its-ow-6b084b242fc7fbfc
land-propose	check:tests/lem-land-review.sh:a-task-that-ran-without-the-owner-is-not-gre-8f2051c7e5ab37b5
land-propose	check:tests/lem-land-review.sh:a-task-that-ran-without-the-owner-with-nothi-eaa1eb014cebc08a
land-propose	check:tests/lem-land-review.sh:the-pull-request-s-checks-say-how-many-commi-41dca83e3532add8
land-propose	check:tests/lem-land-review.sh:with-a-reason-for-each-file-in-the-plan-the-d13ea3e05afa6b96
land-propose	check:tests/lem-land-shop.sh:a-base-that-moved-by-a-document-is-refused-t-15ec8504fb0be0c2
land-propose	check:tests/lem-land-shop.sh:a-plan-of-four-tasks-with-no-plan-talk-is-no-7299403f55c58fb9
land-propose	check:tests/lem-land-shop.sh:a-request-that-came-from-a-bug-names-in-its-d3fd872f37faae7f
land-propose	check:tests/lem-land-shop.sh:a-request-the-owner-called-careful-after-its-8bf78cd8c5c92d4f
land-propose	check:tests/lem-land-shop.sh:a-request-whose-plan-says-careful-is-not-pro-d6ee588cd26e661d
land-propose	check:tests/lem-land-shop.sh:a-talk-s-counts-agree-each-question-of-the-l-af2c7d2fce849072
land-propose	check:tests/lem-land-shop.sh:a-tip-proposed-on-a-base-that-then-went-back-3ffa7e74ec5d19be
land-propose	check:tests/lem-land-shop.sh:after-its-plan-talk-a-plan-of-four-tasks-is-93690b8936d896f6
land-propose	check:tests/lem-land-shop.sh:after-its-plan-talk-a-request-whose-plan-say-e9f24c296b2ca101
land-propose	check:tests/lem-land-shop.sh:the-notes-of-a-careful-request-say-whether-i-a148cb057d8ddc00
land-propose	check:tests/lem-land-shop.sh:the-owner-s-merge-that-a-moved-base-refused-5a18fe00063e45b1
land-propose	check:tests/lem-land-shop.sh:the-pull-request-is-opened-on-github-the-tas-3eba9a0191bd2909
land-propose	check:tests/lem-land-shop.sh:through-a-red-base-the-new-landing-goes-on-w-e7544b70136dee8e
land-review	check:tests/lem-land-shop.sh:a-fix-is-reviewed-only-after-the-machine-che-2ee9e4020def8f4a
land-review	check:tests/lem-land-shop.sh:a-request-that-is-not-careful-with-a-must-fi-47613d70f8d269f3
land-review	check:tests/lem-land-shop.sh:a-request-the-owner-called-careful-gets-the-c7149afffb1ea50b
land-review	check:tests/lem-land-shop.sh:a-review-is-written-down-from-a-file-with-it-3ef9e52577fa06bd
land-review	check:tests/lem-land-shop.sh:a-review-whose-record-is-sent-again-after-a-147c43d34cc7554c
land-review	check:tests/lem-land-shop.sh:nothing-is-proposed-before-its-review-for-a-66c8d8ffc80ab0b9
owner	check:tests/lem-serve.sh:lem-project-waiting-lists-the-rows-of-the-bo-b19e35b08c01192a
sessions	check:tests/lem-land-shop.sh:a-merge-agent-whose-seat-fails-after-the-pul-9ad9f66ba0020edd
sessions	check:tests/lem-machine.sh:a-claim-folder-that-cannot-be-made-still-que-82426ece104d39eb
sessions	check:tests/lem-machine.sh:a-hook-line-with-lem-hook-bin-at-a-file-that-77c47f5908885070
sessions	check:tests/lem-machine.sh:a-hook-line-with-no-lem-hook-bin-and-no-app-f98b86a503650ccf
sessions	check:tests/lem-machine.sh:a-hook-whose-own-directory-was-removed-still-30bc2ef3a51eb4be
sessions	check:tests/lem-machine.sh:each-line-of-hooks-hooks-json-run-through-sh-cfb6e941630ada57
sessions	check:tests/lem-machine.sh:the-hook-does-not-wait-for-its-input-to-clos-0a6f4598d82a6641
sessions	check:tests/lem-machine.sh:the-machine-s-yes-holds-in-each-repository-o-585fa6601d0eba52
sessions	check:tests/lem-machine.sh:the-same-words-in-the-same-session-after-the-54f27fd33cee9442
sessions	check:tests/lem-machine.sh:three-copies-of-the-hook-on-one-message-star-d51cac098de4519e
sessions	check:tests/lem-machine.sh:two-messages-of-one-session-and-one-sentence-bc9b67a5f2740193
sessions	check:tests/lem-machine.sh:when-the-detached-half-cannot-start-the-hook-7b7b8eb14d6a2d0d
sessions	check:tests/lem-machine.sh:with-a-plugin-of-another-version-than-the-ap-db7846b2d42bb9bf
sessions	check:tests/lem-machine.sh:with-the-machine-s-yes-the-hook-prints-nothi-8da58326de71f6bf
sessions	check:tests/lem-machine.sh:without-the-machine-s-yes-no-line-a-no-a-fil-cb04d6eede14e819
sessions	check:tests/test-ask.sh:check:1-c1b43b36df09f0bf
sessions	check:tests/test-ask.sh:stop-hook-is-silent-and-exits-0-outside-agte-d6db9d8e55cfbe96
sessions	check:tests/test-ask.sh:the-plugin-s-stop-hook-silent-exit-0-outside-a2a1af868800d4ed
task	check:tests/lem-decisions.sh:a-dropped-task-stays-dropped-and-its-resume-4cb48ada68901d88
task	check:tests/lem-decisions.sh:a-lead-whose-task-needs-another-task-s-resul-0f3ddd6189435167
task	check:tests/lem-decisions.sh:a-parked-task-gets-no-lead-takes-no-late-sta-a55a45734936af39
task	check:tests/lem-decisions.sh:a-resume-whose-new-worktree-s-setup-fails-ke-d7385594085043ab
task	check:tests/lem-decisions.sh:a-resumed-task-keeps-the-owner-s-approval-af-fad51e2ec671502a
task	check:tests/lem-decisions.sh:a-task-two-releases-back-stops-at-its-first-417a4d8879a707ca
task	check:tests/lem-decisions.sh:his-start-it-for-a-task-queued-behind-a-drop-c3c61905db4d491a
task	check:tests/lem-land-github.sh:a-new-task-s-worktree-starts-from-origin-s-b-5b968321c7a08a7f
task	check:tests/lem-land-github.sh:a-task-is-not-opened-under-a-slug-whose-bran-e7864b74ce3a81d3
task	check:tests/lem-land-shop.sh:a-start-over-moves-the-review-files-of-the-l-6b2c3585e7d05bc1
task	check:tests/lem-land-shop.sh:ready-start-over-over-an-open-task-with-the-8cf1fa3b24b7da9b
task	check:tests/lem-machine.sh:lem-release-before-is-the-version-plugin-jso-38e6d82129bcd310
task	check:tests/lem-serial.sh:a-task-s-new-worktree-gets-checks-setup-one-c87187177cd29b61
task	check:tests/lem-serial.sh:this-repository-s-own-checks-setup-gives-a-t-40d811a6cfd20b89
task	check:tests/lem-settings.sh:a-dropped-task-holds-its-issue-while-it-owes-5aa3c910c1beca45
task	check:tests/lem-settings.sh:a-dropped-task-holds-its-ticket-while-it-owe-258d1c53004db5f8
task	check:tests/lem-settings.sh:a-landed-task-keeps-its-issue-for-good-a-new-56ac93e9239b2431
task	check:tests/lem-settings.sh:a-plan-s-name-is-paths-plan-file-yyyy-mm-dd-ce39bd6563974042
task	check:tests/lem-settings.sh:a-slug-that-is-not-hyphenated-lower-case-wor-da5743990303b154
task	check:tests/lem-settings.sh:a-state-block-that-state-did-not-write-has-n-030a16f62b1f9d0d
task	check:tests/lem-settings.sh:a-state-written-from-the-task-s-worktree-car-97084ca2b041a54f
task	check:tests/lem-settings.sh:a-task-held-for-an-order-that-names-no-task-6f5502e39a2e9a99
task	check:tests/lem-settings.sh:a-task-in-the-landing-or-proposed-takes-no-s-e381983380a127c6
task	check:tests/lem-settings.sh:a-task-is-answered-only-with-its-investigati-bf3b4e870e674a0c
task	check:tests/lem-settings.sh:a-task-keeps-the-ticket-its-ask-came-from-no-70c96591b7aa9405
task	check:tests/lem-settings.sh:an-answered-task-holds-its-ticket-until-the-0eee93cd9bdf0d62
task	check:tests/lem-settings.sh:an-ended-task-stays-ended-no-state-moves-it-7eeee1c148441977
task	check:tests/lem-settings.sh:an-opening-refused-after-its-claim-of-the-is-fe34e3d9093c1835
task	check:tests/lem-settings.sh:an-unknown-task-is-refused-with-the-names-of-7cebab97723b1914
task	check:tests/lem-settings.sh:each-state-block-is-one-event-with-the-ask-a-5226901ff0f6998e
task	check:tests/lem-settings.sh:log-appends-any-other-event-a-number-typed-a-b6613312701116fa
task	check:tests/lem-settings.sh:log-refuses-a-plan-talk-s-record-whose-count-256d245612bb5712
task	check:tests/lem-settings.sh:log-refuses-a-state-event-an-unknown-task-a-b18e8a1658a80ecb
task	check:tests/lem-settings.sh:log-refuses-an-investigation-s-record-in-ano-045cd1994514e99b
task	check:tests/lem-settings.sh:log-takes-a-builder-s-start-in-its-form-and-fffa5dbfe89121c1
task	check:tests/lem-settings.sh:may-start-lets-a-task-start-whatever-builds-81f83a2a97136d8c
task	check:tests/lem-settings.sh:state-prints-the-task-s-first-line-as-say-fo-d5cc5fcd3febc433
task	check:tests/lem-settings.sh:state-puts-a-block-with-the-clock-s-time-abo-6e5c171655a3ae91
task	check:tests/lem-settings.sh:state-refuses-a-status-no-task-has-a-task-th-57d726669b77658e
task	check:tests/lem-settings.sh:state-refuses-a-type-line-without-its-reason-0dee6992653b3228
task	check:tests/lem-settings.sh:state-refuses-the-owner-s-order-a-then-line-0e6d6cfa10059720
task	check:tests/lem-settings.sh:task-dir-ask-keeps-the-owner-s-words-for-the-70208d692053d934
task	check:tests/lem-settings.sh:task-dir-run-in-a-worktree-makes-the-task-s-c1c255515bdb9163
task	check:tests/lem-settings.sh:tasks-says-what-a-landing-proposed-the-pull-470e79c662cae49f
task	check:tests/lem-settings.sh:the-landing-s-own-moves-stay-blocked-landing-385503c7bbd1d814
task	check:tests/lem-settings.sh:ticket-step-assigned-keeps-the-login-on-its-dcfd1e3a05f8ebdc
task	check:tests/lem-settings.sh:ticket-step-writes-each-thing-lem-did-to-a-t-b5983e1972615b93
task	check:tests/lem-settings.sh:with-the-tracker-github-ticket-42-and-ticket-77155207052c74ef
task	check:tests/lem-settings.sh:worktree-dir-names-a-path-under-a-folder-git-1303eda99515f1fa
task	check:tests/lem-settings.sh:worktree-dir-refuses-settings-whose-plans-fo-6e22565f942eb6c2
```

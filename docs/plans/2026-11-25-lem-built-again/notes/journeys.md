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

# What left the list of rulings

Each line below was a ruling of the owner or a choice of the maintaining session, and each is still
in force. It is not a bullet of `docs/rulings/rulings.md` because a test, the code or one text now
holds it. `decided` before a day marks a choice of the maintaining session; every other line is the
owner's ruling, reopened only by asking him, as a bullet of the list is.

The full text of each, with the owner's words, is in git at `04ba08c`, a commit of `main` from
before this change: `git show 04ba08c:docs/rulings/NAME.md`, and for a choice of the session the
same NAME in the folder `.lem/decisions` of that commit, with NAME as the table of
`docs/plans/2026-11-21-rulings-as-one-list.md` names it.

When a test or a place named here stops holding its rule, the rule goes back to the list as a
bullet.

## Held by a test or by the code

- **The question page is a part of Lem, not a tool the machine has or lacks.**
  `tests/unit/settings/doctor/test_command.py::test_without_git_the_check_exits_1_with_its_rows_and_the_refusal_that_names_git`;
  `skills/lem/stages/init.md` (step 6, the question page comes with Lem). (2026-11-14)
- **A task has a type and a track, and they are two words.**
  `tests/unit/task/test_queue.py::test_the_read_keeps_the_type_the_track_and_what_comes_next`;
  `skills/lem/stages/new.md` (the first line). (2026-11-17)
- **Every edit of the settings file is careful.**
  `tests/journeys/landing/test_review.py::test_an_edit_of_lem_s_own_settings_gets_the_full_set_whatever_the_shape_says`. (decided 2026-11-17)
- **A persona's file names its models.**
  `tests/unit/addons/outside/test_cast.py::test_frontmatter_and_copy`. (2026-11-19)
- **Lem brings its own builder agent.**
  `tests/unit/criteria/test_texts.py::test_the_builder_declares_its_model_and_effort_with_no_tool_limit`;
  `agents/lem-builder.md` (its front matter names Opus at high effort);
  `tests/unit/settings/doctor/test_tools.py::test_claude_code_without_the_builder_fails_and_a_builder_file_in_the_home_is_not_lems`;
  `tests/unit/settings/doctor/test_tools.py::test_a_tasks_worktree_finds_the_projects_own_builder_in_the_main_checkout`. (decided 2026-11-14 and 2026-11-15)
- **A plan talk's record is taken as it ran.**
  `tests/unit/task/test_forms.py::test_what_breaks_a_rule_of_the_talk_and_not_a_count_is_taken`. (decided 2026-11-16)
- **A plan never makes a change small.**
  `tests/unit/criteria/test_show.py::test_a_plan_never_puts_a_task_on_the_fast_track`. (decided 2026-11-17)
- **The checks remove what their own commands leave.**
  `tests/journeys/landing/test_checks.py::test_the_checks_remove_what_their_commands_leave`. (decided
  2026-11-17)
- **Without Codex one expert answers alone.**
  `tests/unit/addons/outside/test_experts.py::test_seat_names_and_unavailable_codex`. (2026-11-18)
- **The experts know the personas.**
  `tests/unit/addons/outside/test_experts.py::test_brief_and_shared_pick`. (2026-11-19)
- **A project can close branches.**
  `tests/unit/landing/test_start.py::test_a_protected_task_branch_or_the_base_starts_no_landing`;
  `src/lem/model/landing/invariants.py` (the protection for pushes, merges and deletes). (2026-11-14)
- **After a merge, Lem repairs only a pull request with a conflict.**
  `tests/unit/board/duties/test_wakes.py::test_after_a_merge_an_open_task_with_no_conflict_waits_as_it_is`. (2026-11-17)
- **`branch.history` is `"squash"` by default.**
  `tests/unit/settings/test_load.py::test_with_no_file_every_value_is_lems_default`. (2026-11-18)
- **A polish pass is a step of the flow.**
  `tests/journeys/landing/test_checks.py::test_the_polish_pass_keeps_its_start_and_its_run_which_the_checks_take`. (2026-11-16)
- **A partial review is a review.**
  `tests/unit/landing/test_review.py::test_a_partial_review_is_a_review_and_keeps_who_did_not_answer`. (2026-11-16)
- **A lowered bar (a new suppression, a skipped or deleted test, fewer assertions) makes a pull request not green also when the plan gives its reason.**
  `tests/unit/landing/test_green.py::test_checks_the_branch_brought_a_lowered_bar_and_a_red_run_are_not_green`;
  `tests/unit/landing/test_bar.py` (the kinds of reduction in the bar). (decided 2026-11-16)
- **A small change never gets a polish pass.**
  `tests/journeys/landing/test_fast_track.py::test_the_fast_track_checks_its_criterion_once_and_lands`;
  `skills/lem/prompts/small.md` (the fast-track builder). (decided 2026-11-16, 2026-11-17)
- **His away status is one mark of the machine, and a night task always runs without him.**
  `tests/unit/owner/test_presence.py::test_back_takes_back_every_task_but_a_nights`. (2026-11-19)
- **Inside a phase a session compacts itself at his number, for all his repositories.**
  `tests/contract/test_harness.py::test_the_compaction_number_is_the_machines_and_zero_leaves_it_out`. (2026-11-21)
- **The backlog is a part of Lem, and its view is a tab of the board.**
  `tests/unit/board/views/test_backlog_view.py::test_the_filter_of_the_address_turns_its_chip_on_and_a_second_press_off`. (2026-11-15)
- **An address for each workspace and task, two machines under one, and pushes.**
  `tests/journeys/test_server.py::test_lem_board_gives_a_tasks_address_and_marks_example_tasks_for_good`;
  `tests/journeys/test_peers.py` (the joined workspaces);
  `tests/unit/board/service/test_push.py` (the pushes). (2026-11-20)
- **He acts from the board.**
  `tests/journeys/test_acts.py::test_his_approval_from_the_confirm_step_lands_the_pull_request_as_his_word`. (2026-11-20)
- **A seat is written `agent/model:effort`**
  The reviewer's too, and each of the three seats is written whole.
  `tests/unit/settings/test_load.py::test_a_seat_that_does_not_read_by_its_rule_is_refused`. (2026-11-17, 2026-11-18)
- **The state of Lem is not in the git directory.**
  `tests/unit/task/test_open.py::test_from_a_tasks_worktree_the_state_is_the_main_checkouts`. (2026-11-17)
- **Not every section of the settings stays.**
  `tests/unit/settings/test_load.py::test_a_table_or_key_out_of_place_is_refused_with_the_place_or_the_nearest`. (2026-11-18)
- **`[checks]` keeps three keys, and `alone` is `serial`.**
  `tests/unit/settings/test_init.py::test_the_file_init_writes_holds_every_key_of_the_teams_file`. (2026-11-18)
- **Three places are settings**
  The plans folder, a plan's file name and the rulings file. A plan's file is
  `YYYY-MM-DD-<slug>.md` unless the settings say otherwise.
  `tests/unit/settings/test_init.py::test_path_gives_one_absolute_path_from_any_folder_of_the_checkout`. (2026-11-17, 2026-11-18, 2026-11-22)
- **One machine may name its own reviewer for a while.**
  `tests/unit/settings/test_set.py::test_set_local_writes_a_whole_seat_and_says_where_it_comes_from`. (decided 2026-11-14 and 2026-11-15)
- **As a plugin, the correction hook comes with the install.**
  `tests/hooks/test_manifest.py::test_the_manifest_registers_each_selector_on_its_event_matcher_and_flags`. (2026-11-15)
- **The Jev model comes through any provider.**
  `tests/unit/addons/outside/test_jev.py::test_provider_uses_only_jev_key_and_never_sends_during_check`. (2026-11-18)
- **A correction hook registered twice judges each message once.**
  `tests/hooks/test_corrections.py::test_a_hook_registered_twice_judges_each_message_once`. (decided 2026-11-17)

## Kept in one place

- **A release is a change of the plugin's `version`.** `AGENTS.md` ("A release"); the value is in
  `.claude-plugin/plugin.json`. (2026-11-20)
- **A shipped skill's name follows `/lem`.** `AGENTS.md` ("Rules for a change here", "A stage names
  a capability or a role, never a tool"). (2026-11-14)
- **The session's answers to his notes that asked a question: `[gate]` is renamed `[checks]`, a lead
  queues a task behind another open task whose result it needs, and the plugin's commands carry
  Lem's name.** `docs/settings.md` ("`[checks]`"); `skills/lem/stages/plan.md` (the paragraph before
  step 1); `AGENTS.md` ("A stage names a capability or a role, never a tool"). (decided 2026-11-17)
- **`/lem build` takes a plan file too, and lists the waiting plans when it gets no name.**
  `skills/lem/stages/start.md` ("`/lem build`"). (decided 2026-11-14 and 2026-11-15)
- **The size of a change decides its path.** `skills/lem/SKILL.md` (its opening, the fast track);
  `skills/lem/prompts/small.md`. (decided 2026-11-17)
- **The commands of his status and of a task are `/lem im-away`, `/lem im-back`, `/lem be-careful
  [task]`, `/lem standard-track [task]` and `/lem drop [task]`.** `skills/lem/SKILL.md`
  ("Subcommands", the rows `im-away`, `im-back` and `be-careful`, `standard-track`, `drop`).
  (2026-11-18)
- **The investigation of a bug keeps its method.** `skills/lem/prompts/investigator.md` (step 2,
  "Find the cause", the `lem-root-cause` method). (2026-11-18)
- **A full change has one approval and no ceremony that nobody asked for.**
  `skills/lem/stages/interview.md` (step 2, the interview: its restate and its yes are the criteria
  and his yes to them). (decided 2026-11-17)
- **A criterion a persona doubted stays as written until the owner sees it.**
  `skills/lem/stages/interview.md` (step 6, "His yes": "Never reword it before he sees it").
  (decided 2026-11-16)
- **The plan talk is predictably short, over a closed list.** `skills/lem/stages/talk.md` (its
  rules: the list closes with the reviewer's first turn, a question that holds a second time stops).
  (2026-11-16)
- **A plan may end with a documentation task.** `skills/lem/stages/plan.md` (step 1, the
  documentation task, last). (2026-11-16)
- **No CI on a push for now.** `.github/workflows/ci.yml` (its comment and `on: workflow_dispatch`).
  (2026-11-17)
- **The tests are chosen by what can fail, and a task is quick**: the tests are to be useful and
  fast. `AGENTS.md` ("Checks", the loop). (2026-11-18, 2026-11-19)
- **Two builders of one plan that run at one moment commit only their own paths.**
  `agents/lem-builder.md` (rules 5 and 10). (decided 2026-11-21)
- **A choice that matters is logged, also when nobody was asked.** `skills/lem/stages/ladder.md`
  (its opening: log it with `--by lead`). (2026-11-18)
- **`/lem ask-expert` takes a question in words, or none.** `skills/lem-ask-expert/SKILL.md` ("Which
  question"). (2026-11-17)
- **A decision of the plan does not hold the task: `held` keeps what has no options, the criteria
  that wait for his yes, one more fact for an investigation and a step that is his to do.**
  `skills/lem/SKILL.md` ("Where a task keeps its state", the row `held`). (decided 2026-11-16)
- **A machine failure stops a task as `blocked`, with one line that names what to do, and with no
  breaker's document.** `skills/lem/SKILL.md` ("Where a task keeps its state", the row `blocked`).
  (decided 2026-11-21)
- **The push and the pull request of `propose` need no question.** `skills/lem/stages/land.md` (step
  6, `propose`). (decided 2026-11-17)
- **The board's server runs the merge agent's merge, and the agent only writes its review.**
  `src/lem/board/duties/merge.py` (the merge duty). (decided 2026-11-21)
- **The status knows what merged, and changes only what already happened.**
  `skills/lem/stages/status.md` (its opening: what merged on GitHub is the board's server's, and the
  status only reads). (decided 2026-11-17)
- **Nobody else's word is his.** `skills/lem/stages/land.md` (step 8, "The merge", `--by owner`).
  (decided 2026-11-18)
- **Lem composes the first line of a task, and its session says it as it is.**
  `src/lem/app/tasks/first_line.py` (the first line); `skills/lem/prompts/session.md` (the opening
  of the session). (decided 2026-11-21)
- **The trials of 2026-11-21: a task's session says its first line first, and the onboarding
  writes no allow rules and commits the plugin's file.** `skills/lem/prompts/session.md` ("What
  comes next");
  `skills/lem/stages/init.md` (steps 4 and 6). (decided 2026-11-21)
- **A board of example tasks says so on the page, and a line that waits for him says where he answers.**
  `src/lem/board/templates/sidebar.html` (the notice); `src/lem/board/views/waits/` (where the
  owner answers). (2026-11-14)
- **The time card gets exact start times.**
  `src/lem/model/task/spans.py` (the start and end of a span); `src/lem/board/views/timeline/` (the time card). (2026-11-17)
- **What waits for the owner is one list, with a decision for each item.** `skills/lem/SKILL.md`
  ("Subcommands", the row bare `/lem`, `status`); `skills/lem/stages/status.md`. (2026-11-17)
- **A chord opens a list of the tasks.** `src/lem/addons/picker/picking.py` (its module docstring).
  (2026-11-18)
- **A page to read opens as a companion.**
  `src/lem/cli/board/command.py` (the call of the board); `skills/lem/harness/claude-code/show-page.md` (a page to read). (2026-11-18)
- **No stale pull request, and a folded header on a phone.**
  `src/lem/board/views/merge_state.py` (the look at the forge); `src/lem/board/templates/task/` (the task panel). (2026-11-20)
- **A task's artifacts have one map.**
  `src/lem/board/views/artifacts/` (the map of the files and records). (2026-11-20)
- **The board is served, and the server draws it.**
  `src/lem/board/app.py` (the board app); `skills/lem/SKILL.md` ("The board"). (decided 2026-11-20)
- **A check of the tracker is no command of the owner's.** `skills/lem-linear/SKILL.md` ("check").
  (2026-11-14)
- **`/lem read KEY` shows a ticket.** `skills/lem/SKILL.md` ("Subcommands", the row `read
  <ticket>`). (2026-11-19)
- **Onboarding asks three questions.** `skills/lem/stages/init.md` ("3. Three questions"). (decided
  2026-11-17)
- **The README tells a command he types from one a job or Lem runs.** `docs/index.md` ("What you
  type"), the home page of the site. (2026-11-14)
- **The texts assume a public repository.** `README.md` ("Install": no step for access);
  `docs/install.md` ("Install"). (2026-11-17)
- **The README says a plugin that works closely with agterm, and names no operating system.**
  `README.md` (its opening); `docs/index.md` (its opening). (2026-11-18)
- **Each label of a chart is quoted.** `AGENTS.md` ("Documentation describes the current state");
  `skills/lem/prompts/writing.md` ("The flowchart") for a task's documents. (2026-11-19)
- **The texts people read say "the owner".** `AGENTS.md` ("The app is Python 3.14 on the
  well-known library for each job, and its texts say "the owner""). (decided 2026-11-17)
- **A night's brake: with two or more of its pull requests that nobody merged or closed, a night
  opens nothing.** `skills/lem/stages/night.md` (step 1, "The brake"). (decided 2026-11-18)

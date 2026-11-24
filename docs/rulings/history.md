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
  `tests/lem-machine.sh: "the check has no row for the question page, which is a part of Lem"`; no
  page for the owner lists it: `skills/lem/stages/init.md` (step 6, "the question page comes with
  Lem"). (2026-11-14)
- **A task has a type and a track, and they are two words.**
  `tests/unit/test_task_rules.py::TypeLine.test_each_of_the_eight_types_is_taken`;
  `tests/unit/test_task.py::FirstLine.test_the_fast_track_quotes_its_criterion`;
  `tests/lem-settings.sh: "a plan with no criteria section, no size, a small change of two
  criteria"`; careful is a mark on top, the line `careful:` of the first state block:
  `skills/lem/stages/new.md` ("The request", step 1). (2026-11-17)
- **Every edit of the settings file is careful.** `tests/lem-land-review.sh: "every edit of Lem's
  own settings is careful by the script"` (decided 2026-11-17)
- **A persona's file names its models.**
  `tests/unit/test_cast.py::Seats.test_a_file_names_its_seats_each_with_its_parts_and_its_name`;
  `tests/unit/test_cast.py::Seats.test_a_file_with_no_seats_answers_as_the_panel_always_did`;
  `tests/test-gate-panel.sh: "a persona's frontmatter names its seats and its agent reads the file
  without it"` (2026-11-19)
- **Lem brings its own builder agent.** `tests/lem-machine.sh: "the builder's definition names its
  model and effort, and no tool list"`; `tests/lem-machine.sh: "a machine with Claude Code and no
  lem-builder agent fails the check"`; `tests/lem-machine.sh: "in a task's worktree the check finds
  a project's own builder in the main checkout"`; on Opus at high effort: `agents/lem-builder.md`
  (its front matter, `model: opus`, `effort: high`). (decided 2026-11-14 and 2026-11-15)
- **A plan talk's record is taken as it ran.** `tests/lem-land-shop.sh: "a talk's counts agree: each
  question of the list ends settled or open"`; `tests/lem-land-shop.sh: "after its plan talk a plan
  of four tasks is proposed, and its text holds"` (decided 2026-11-16)
- **A plan never makes a change small.** `tests/lem-land-local.sh: "a plan that says Size: small is
  refused by the criteria, the polish pass"` (decided 2026-11-17)
- **The checks remove what their own commands leave.** `tests/lem-land-guards.sh: "a gate command
  that writes a cache folder and a file git does not know passes"`; `tests/lem-land-guards.sh: "a
  file that was untracked before the gate is not removed"`; `tests/lem-land-guards.sh: "the gate
  refuses a command that edits a tracked file, one that makes a commit"`; onboarding proposes the
  ignore lines for what the commands leave: `skills/lem/stages/init.md` (step 4). (decided
  2026-11-17)
- **Without Codex one expert answers alone.** `tests/test-ask-expert.sh: "with no Codex on the
  machine one expert answers alone"`;
  `tests/unit/test_settings.py::Seats.test_an_expert_is_here_when_its_agent_is_on_the_machine`;
  `tests/lem-settings.sh: "init with --codex no, for a machine with no Codex, writes the reviewer's
  whole seat"` (2026-11-18)
- **The experts know the personas.**
  `tests/unit/test_experts.py::Audience.test_the_part_names_the_profile_and_each_persona_by_its_path_and_says_how_to_weigh_them`;
  `tests/test-ask-expert.sh: "a brief names the profile and each persona by its path, heading and
  who they are"` (2026-11-19)
- **A project can close branches.** `tests/lem-land-shop.sh: "no step runs toward a branch the
  settings refuse"`; `tests/lem-land-guards.sh: "a task branch the owner protected after its
  worktree was made gets no push from propose"`; `tests/lem-settings.sh: "may-land refuses a
  protected branch, any branch but the base"` (2026-11-14)
- **After a merge, Lem repairs only a pull request with a conflict.** `tests/lem-land-github.sh:
  "after a merge an open task with no conflict waits as it is"`; `tests/lem-land-github.sh: "a
  conflict after a merge: base stops on the files of the pull request"`; `tests/lem-board-act.sh:
  "after GitHub merged a pull request the server runs lem land merged"` (2026-11-17)
- **`branch.history` is `"squash"` by default.**
  `tests/unit/test_settings.py::Values.test_a_branch_defaults_to_squash_and_the_merge_agent`
  (2026-11-18)
- **A polish pass is a step of the flow.** `tests/lem-land-review.sh: "a full change's checks waits
  for the polish pass"` (2026-11-16)
- **A partial review is a review.** `tests/lem-land-shop.sh: "a request the owner called careful
  gets the project's full set"`; `tests/lem-land-local.sh: "a full change with no read of its
  criteria is not proposed"`; `tests/lem-land-review.sh: "a change of documentation only is not
  proposed without a review"` (2026-11-16)
- **A lowered bar (a new suppression, a skipped or deleted test, fewer assertions) makes a pull
  request not green also when the plan gives its reason.** `tests/lem-land-review.sh: "with a reason
  for each file in the plan the gate passes"`;
  `tests/unit/test_land.py::Bar.test_fewer_assertions_in_a_test_file`;
  `tests/unit/test_land.py::Bar.test_a_deleted_test_file_is_one_entry`;
  `tests/unit/test_land.py::Bar.test_a_skip_of_a_whole_module` (decided 2026-11-16)
- **A small change never gets a polish pass.** `tests/lem-land-small.sh: "a small change whose
  builder filed a defect outside it in its own commit has no polish pass"`; its builder fixes a cheap
  defect outside it in a commit of its own, and files only one over the bar of rule 6:
  `skills/lem/prompts/small.md` (step 7). (decided 2026-11-16, 2026-11-17)
- **His away status is one mark of the machine, and a night task always runs without him.**
  `tests/lem-state.sh: "the owner's status is one mark of the machine: with none he is there"`;
  `tests/unit/test_owner.py::Spans.test_a_back_ends_his_away_and_never_a_night`;
  `tests/lem-decisions.sh: "a task the night opened runs without the owner and carries the night's
  date in tasks"` (2026-11-19)
- **Inside a phase a session compacts itself at his number, for all his repositories.**
  `tests/unit/test_session.py::Tokens.test_absent_is_lems_number_and_zero_sets_nothing`;
  `tests/unit/test_session.py::Tokens.test_under_the_floor_a_negative_a_bool_and_a_float_are_refused`;
  `tests/lem-session.sh: "open makes one session of the task in the caller's workspace, with no
  focus"` (2026-11-21)
- **The backlog is a part of Lem, and its view is a tab of the board.** `tests/lem-serve.sh: "the
  backlog's filter comes from the address: its words in the field and its chip on"`;
  `tests/lem-settings.sh: "the board's backlog has each item with its worth"`;
  `tests/lem-board-act.sh: "a new task starts from the board: the owner's words name it"`
  (2026-11-15)
- **An address for each workspace and task, two machines under one, and pushes.**
  `tests/lem-serve.sh: "a task's Overview and each of its tabs and each view answer"`;
  `tests/lem-peers.sh: "--join asks the machine once and writes it into [peers]"`;
  `tests/unit/test_push.py::Sending.test_a_row_gained_while_the_owner_is_away_is_sent_and_a_demo_sends_nothing`
  (2026-11-20)
- **He acts from the board.** `tests/lem-board-act.sh: "through the door another login is refused,
  and the owner's yes is the owner's approval"`; `tests/lem-board-act.sh: "a merge runs only from
  its confirm step, which says green first"`; `tests/lem-board-act.sh: "a park from the board writes
  the state parked with the owner's line of why"` (2026-11-20)
- **A seat is written `agent/model:effort`**, the reviewer's too, and each of the three seats is
  written whole. `tests/unit/test_settings.py::Seats.test_the_seats_it_refuses`;
  `tests/unit/test_settings.py::Seats.test_each_of_the_three_is_refused_unless_whole`;
  `tests/unit/test_settings.py::UnknownNames.test_a_seat_written_as_a_table_with_the_seat_form`
  (2026-11-17, 2026-11-18)
- **The state of Lem is not in the git directory.** `tests/lem-state.sh: "the state is in .lem/state
  of the main checkout, also for a script run"` (2026-11-17)
- **Not every section of the settings stays.** `tests/lem-settings.sh: "the team's file holds 21
  keys, the same in show, in the file init writes"`; `tests/lem-machine.sh: "a new settings file has no
  [tools]: Lem asks with its own page"`;
  `tests/unit/test_settings.py::UnknownNames.test_a_key_of_paths_with_the_keys_it_knows`
  (2026-11-18)
- **`[checks]` keeps three keys, and `alone` is `serial`.** `tests/lem-settings.sh: "the settings
  init writes name every key show prints under [checks]"`;
  `tests/unit/test_settings.py::Values.test_a_branch_defaults_to_squash_and_the_merge_agent`;
  `tests/lem-serial.sh: "the checks run each checks.serial command after checks.commands, under the
  one lock"` (2026-11-18)
- **Three places are settings**: the plans folder, a plan's file name and the rulings file. A
  plan's file is `YYYY-MM-DD-<slug>.md` unless the settings say otherwise.
  `tests/unit/test_settings.py::UnknownNames.test_a_key_of_paths_with_the_keys_it_knows`;
  `tests/lem-settings.sh: "the rulings file is a setting"`;
  `tests/lem-settings.sh: "a plan's name is paths.plan_file, YYYY-MM-DD-<slug>.md by default"`
  (2026-11-17, 2026-11-18, 2026-11-22)
- **One machine may name its own reviewer for a while.** `tests/lem-settings.sh: "set local
  reviewer AGENT/MODEL:EFFORT, run in a worktree, writes this machine's seat in the main checkout"`;
  `tests/lem-settings.sh: "set local reviewer default gives the project's reviewer back and keeps
  what else the machine set"`; `tests/lem-settings.sh: "the machine's own file may not hold the checks or any
  other rule of the project"` (decided 2026-11-14 and 2026-11-15)
- **As a plugin, the correction hook comes with the install.** `tests/lem-machine.sh: "the plugin
  manifest names lem and a version of three numbers, which is the release"` (2026-11-15)
- **The Jev model comes through any provider.** `tests/lem-machine.sh: "lem jev takes its key from
  JEV_API_KEY alone, and with a key under another name"` (2026-11-18)
- **A correction hook registered twice judges each message once.** `tests/lem-machine.sh: "three
  copies of the hook on one message, started at once as three registrations"` (decided 2026-11-17)

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
  `src/lem/serve.py` (its module docstring, the duty `merge_due`). (decided 2026-11-21)
- **The status knows what merged, and changes only what already happened.**
  `skills/lem/stages/status.md` (its opening: what merged on GitHub is the board's server's, and the
  status only reads). (decided 2026-11-17)
- **Nobody else's word is his.** `skills/lem/stages/land.md` (step 8, "The merge", `--by owner`).
  (decided 2026-11-18)
- **The first line of a task is composed by `lem project state`, and its session says it as it is.**
  `src/lem/project.py` (`opening_line`); `skills/lem/prompts/session.md` ("What comes
  next"). (decided 2026-11-21)
- **The trials of 2026-11-21: a task's session says its first line first, and the onboarding
  writes no allow rules and commits the plugin's file.** `skills/lem/prompts/session.md` ("What
  comes next");
  `skills/lem/stages/init.md` (steps 4 and 6). (decided 2026-11-21)
- **A board of example tasks says so on the page, and a line that waits for him says where he
  answers.** `src/lem/board_pages.py` (the demo notice, and `wait_row`). (2026-11-14)
- **The time card gets exact start times.** `skills/lem/SKILL.md` ("Where a task keeps its state", a
  stage's start is an event); `STARTS` in `src/lem/project.py`. (2026-11-17)
- **What waits for the owner is one list, with a decision for each item.** `skills/lem/SKILL.md`
  ("Subcommands", the row bare `/lem`, `status`); `skills/lem/stages/status.md`. (2026-11-17)
- **A chord opens a list of the tasks.** `src/lem/picker.py` (its module docstring).
  (2026-11-18)
- **A page to read opens as a companion.** `src/lem/board.py` (its module docstring).
  (2026-11-18)
- **No stale pull request, and a folded header on a phone.** `src/lem/serve.py` (its
  module docstring, the look at the forge); `src/lem/board_task.py` (`head`).
  (2026-11-20)
- **A task's artifacts have one map.** `src/lem/artifacts.py` (its module docstring).
  (2026-11-20)
- **The board is served, and the server draws it.** `src/lem/serve.py` (its module
  docstring); `skills/lem/SKILL.md` ("The board"). (decided 2026-11-20)
- **A check of the tracker is no command of the owner's.** `skills/lem-linear/SKILL.md` ("check").
  (2026-11-14)
- **`/lem read KEY` shows a ticket.** `skills/lem/SKILL.md` ("Subcommands", the row `read
  <ticket>`). (2026-11-19)
- **Onboarding asks three questions.** `skills/lem/stages/init.md` ("3. Three questions"). (decided
  2026-11-17)
- **The README tells a command he types from one a job or Lem runs.** `README.md` ("What you type",
  "Skills you can call"). (2026-11-14)
- **The texts assume a public repository.** `README.md` ("Install": no step for access).
  (2026-11-17)
- **The README says a plugin that works closely with agterm, and names no operating system.**
  `README.md` (its opening). (2026-11-18)
- **Each label of a chart is quoted.** `AGENTS.md` ("Documentation describes the current state");
  `skills/lem/prompts/writing.md` ("The flowchart") for a task's documents. (2026-11-19)
- **The texts people read say "the owner".** `AGENTS.md` ("Scripts are standard-library Python, 3.11
  or newer"). (decided 2026-11-17)
- **A night's brake: with two or more of its pull requests that nobody merged or closed, a night
  opens nothing.** `skills/lem/stages/night.md` (step 1, "The brake"). (decided 2026-11-18)

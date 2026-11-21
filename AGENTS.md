# Lem

Lem is the `lem` skill and the skills it ships: one flow for a unit of work in any repository, with each project's settings kept
in that project's repository. `README.md` says what it does, the pages in `docs/` say how it
works, and this file says how to change it.

## Rules for a change here

- **The skill knows no project.** No repository, product, path or person of a real project appears
  in `skills/lem/SKILL.md`, the stage files, the harness files or the templates, except as the
  dated source of a measurement ("convertiser-server, 2026-11-14"). What a project needs to say,
  it says in its own `.lem/` folder or its own `AGENTS.md`.
- **A stage names a capability or a role, never a tool.** `spawn-builder`, `second-opinion`,
  `ask-owner`, `fan-out`, `show-page`, `load-skill`; the question gate, the persona panel, the
  review tool. `skills/lem/harness/README.md` is the contract. A tool's name belongs in the one
  harness file of its agent. A skill this repository ships is named by its name, which is the
  same in every agent.
- **A harness file exists only for an agent the contract was checked in.** Do not write one from
  another project's notes about an agent.
- **A number in a skill file carries its source and date.** A rule that rests on a measurement
  says so; a rule that rests on a guess says that instead (`READ_AT` in `land.py`).
- **One stage file per subcommand, read only when it runs, and a part that only one path reads
  is a file of its own.** `SKILL.md` holds what is true in every stage. A rule that one stage
  needs goes in that stage. A part of a stage that only one of its paths needs (the interview,
  an investigation, the polish pass) is a file beside it, and the step that chooses the path
  names that file in one line: a task on the fast track reads nothing that only the standard track needs.
- **A task's phases stay apart.** `plan` and `build` are the lead's, in the build phase. A step
  that reads a task's code or its diff goes to the lead, a builder or a fresh agent (the
  investigator, the review, the merge agent), never into the shape (`new`, `interview`) or the
  landing (`land`).
- **Scripts are standard-library Python, 3.11 or newer**, print JSON for an agent to read, and
  refuse a wrong input with exit 1 and a message that names the fix. No silent default for a
  choice that is the owner's (`project.py init` with no base it can tell asks for `--base`).
- **A change is measured by what it costs a developer on a small task** (the touches it asks of
  him, the waits, the agents it starts) as well as by what it guards.
- **Documentation describes the current state.** No changelog paragraphs, no "previously".
- **A maintainer's session with nobody at the terminal reads `docs/free-hour.md` first.** It works in a
  worktree of this clone, on a branch, and never pushes: `main` of this repository is what every
  project's next update of the plugin installs. The scheduled
  `/lem night` of this repository is such a session too, and it opens no task here: asked on
  2026-11-21 whether a night here may open pull requests, the owner answered "A3 no".
- **Lem is not released, so a change keeps no reading of the form before it.** A change to the
  settings, a record, an event, a state or a command reads and writes the new form only, and the
  maintaining session corrects the repositories that use Lem by hand. When Lem has users, this
  rule changes.
- **Before a change that reaches what a sentence of the two lists below names, read that
  sentence's file**, in whatever group it stands. A sentence names its ruling, and the sentences of
  "What Lem is, and who it is for" name what Lem holds and leaves out, so a change that adds a part
  to Lem (a skill, a hook, a command, a key of the settings, a tool it needs) reaches each of them.
- **A new ruling of the owner is a file of `docs/rulings/` and one sentence in `AGENTS.md`.**
  `lem project ruling-file SLUG` names the file, from the words of the sentence in lower case with
  hyphens. The file opens with a front matter block of `ruled:` (his day) and `area:` (the heading
  of its group), then the sentence as its `#` title, then the ruling in his words. The sentence is
  the text of a link to the file, alone on its line under the heading of its group. The file and
  the sentence change in the same commit.
- **A ruling that replaces another takes that ruling's file whole**, with its own `## Changed in
  part` and `## Replaced, not in force`, into its own `## Replaced, not in force`: a `###` heading
  of the replaced sentence, the line `Ruled on DAY.`, then its text. The replaced file and its
  sentence leave, and each link to the removed file, in `AGENTS.md` and in the two folders, names
  the new file in the same commit.
- **A ruling that changes a part of another changes that ruling's sentence and title where they
  are no longer true**, and adds one line to that ruling's `## Changed in part`: the day, the new
  ruling's sentence as a link, and the part it changed. A file with no `## Changed in part` yet
  gets one under its title, opening with "The title is the rule as it stands. Where the paragraph
  below says otherwise, the line here holds.", and its old words go under `## As ruled on DAY,
  changed in part since`.
- **A new decision of the maintaining session is a file of `.lem/decisions/`**, named as a
  ruling's file is, with `decided:` in place of `ruled:`, and one sentence under the heading of
  its group in "Decisions the maintaining session took". A decision changes as a ruling does, and
  no heading or marker line of its file says "ruled": `decided:`, `Decided on DAY.` and `## As
  decided on DAY, changed in part since` take the place of a ruling's words. A moved paragraph
  keeps its words, "ruled" among them. A decision that a ruling replaces keeps its file,
  whose first line under the title is `Replaced, not in force: on DAY, by` and the link of that
  ruling, and the ruling's `## Replaced, not in force` links it back.

## The owner's rulings

Each sentence below is a ruling of the owner in force, and the text of a link to its file in
`docs/rulings/`, which holds his words, the day, what changed it since and what it replaced. A
ruling is reopened only by asking him.

### What Lem is, and who it is for

- [Lem is for experienced developers, and every change is measured against that](docs/rulings/lem-is-for-experienced-developers-and-every-change-is-measured-against-that.md)
- [One Lem for one repository.](docs/rulings/one-lem-for-one-repository.md)
- [Claude Code first.](docs/rulings/claude-code-first.md)
- [Opinionated and small.](docs/rulings/opinionated-and-small.md)
- [The rules of an existing project stay where they are](docs/rulings/the-rules-of-an-existing-project-stay-where-they-are.md)
- [Another program's settings stay where that program keeps them](docs/rulings/another-programs-settings-stay-where-that-program-keeps-them.md)
- [webrev is the way to mark up a plan or a document, a required recipe of the agterm cookbook, and it is not a part of Lem.](docs/rulings/webrev-is-the-way-to-mark-up-a-plan-or-a-document-a-required-recipe-of-the-agterm-cookbook-and-it-is-not-a-part-of-lem.md)
- [Lem is a plugin, and nothing else](docs/rulings/lem-is-a-plugin-and-nothing-else.md)
- [Lem is his one desk for work in a repository, and its core is the path from a request to a merged pull request.](docs/rulings/lem-is-his-one-desk-for-work-in-a-repository-and-its-core-is-the-path-from-a-request-to-a-merged-pull-request.md)
- [Release, last-tag and the review of another person's pull request leave the core](docs/rulings/release-last-tag-and-the-review-of-another-persons-pull-request-leave-the-core.md)
- [Three more commands are no commands of his, and two recipes of the agterm cookbook become required](docs/rulings/three-more-commands-are-no-commands-of-his-and-two-recipes-of-the-agterm-cookbook-become-required.md)
- [No word and no form of a Lem before is kept.](docs/rulings/no-word-and-no-form-of-a-lem-before-is-kept.md)
- [The user of Lem is a senior developer with little attention to give](docs/rulings/the-user-of-lem-is-a-senior-developer-with-little-attention-to-give.md)
- [The shipped skills are for the times he steps in](docs/rulings/the-shipped-skills-are-for-the-times-he-steps-in.md)
- [Claude Code and agterm first, and Codex for reviews](docs/rulings/claude-code-and-agterm-first-and-codex-for-reviews.md)

### What Lem needs on the machine

- [agterm is a hard dependency](docs/rulings/agterm-is-a-hard-dependency.md)
- [The question page is a part of Lem, not a tool the machine has or lacks](docs/rulings/the-question-page-is-a-part-of-lem-not-a-tool-the-machine-has-or-lacks.md)
- [agterm, the mailbox chat and revmux stay required](docs/rulings/agterm-the-mailbox-chat-and-revmux-stay-required.md)
- [cronn is required, and Codex is highly recommended](docs/rulings/cronn-is-required-and-codex-is-highly-recommended.md)
- [Lem assumes auto mode](docs/rulings/lem-assumes-auto-mode.md)
- [A release is a change of the plugin's `version`](docs/rulings/a-release-is-a-change-of-the-plugins-version.md)
- [Python 3.11 stays, in the modern form.](docs/rulings/python-3-11-stays-in-the-modern-form.md)

### A request: its type, its track and its commands

- [A shipped skill's name follows `/lem`](docs/rulings/a-shipped-skills-name-follows-lem.md)
- [What must not go wrong is named by topic, and an agent says whether a task is careful](docs/rulings/what-must-not-go-wrong-is-named-by-topic-and-an-agent-says-whether-a-task-is-careful.md)
- [Lem tells the type of a request, asks when it is unclear, and a bug is investigated first](docs/rulings/lem-tells-the-type-of-a-request-asks-when-it-is-unclear-and-a-bug-is-investigated-first.md)
- [A task has a type and a track, and they are two words.](docs/rulings/a-task-has-a-type-and-a-track-and-they-are-two-words.md)
- [The first line is where he corrects Lem's read of a request](docs/rulings/the-first-line-is-where-he-corrects-lems-read-of-a-request.md)
- [The two tracks are the fast track and the standard track](docs/rulings/the-two-tracks-are-the-fast-track-and-the-standard-track.md)
- [A helper starts from plain words](docs/rulings/a-helper-starts-from-plain-words.md)
- [The commands of his status and of a task are `/lem im-away`, `/lem im-back`, `/lem be-careful [task]`, `/lem standard-track [task]` and `/lem drop [task]`.](docs/rulings/the-commands-of-his-status-and-of-a-task-are-lem-im-away-lem-im-back-lem-be-careful-task-lem-standard-track-task-and-lem-drop-task.md)
- [The investigation of a bug keeps its method](docs/rulings/the-investigation-of-a-bug-keeps-its-method.md)
- [A task order in his words stays](docs/rulings/a-task-order-in-his-words-stays.md)

### The interview, the criteria and the personas

- [The personas' read of the acceptance criteria is his to skip, and only when every criterion names only the developer](docs/rulings/the-personas-read-of-the-acceptance-criteria-is-his-to-skip-and-only-when-every-criterion-names-only-the-developer.md)
- [Every project of Lem has personas, and a panel asks the project's own](docs/rulings/every-project-of-lem-has-personas-and-a-panel-asks-the-projects-own.md)
- [One approved line of a task is an acceptance criterion](docs/rulings/one-approved-line-of-a-task-is-an-acceptance-criterion.md)
- [A complete ticket that someone else wrote needs his yes to its criteria, and no interview](docs/rulings/a-complete-ticket-that-someone-else-wrote-needs-his-yes-to-its-criteria-and-no-interview.md)
- [A persona's file names its models](docs/rulings/a-personas-file-names-its-models.md)
- [Most requests have an interview and his check of the acceptance criteria, and the pull request says green or not green first.](docs/rulings/most-requests-have-an-interview-and-his-check-of-the-acceptance-criteria-and-the-pull-request-says-green-or-not-green-first.md)
- [The personas read first, and their confusion may change the design](docs/rulings/the-personas-read-first-and-their-confusion-may-change-the-design.md)

### The plan, the build and the tests

- [The first run is in a scratch repository](docs/rulings/the-first-run-is-in-a-scratch-repository.md)
- [Each task of a plan gets a fresh builder](docs/rulings/each-task-of-a-plan-gets-a-fresh-builder.md)
- [The plan talk is predictably short, over a closed list](docs/rulings/the-plan-talk-is-predictably-short-over-a-closed-list.md)
- [The plan talk is a pair in a companion that closes after it](docs/rulings/the-plan-talk-is-a-pair-in-a-companion-that-closes-after-it.md)
- [A plan's file is `YYYY-MM-DD-<slug>.md`](docs/rulings/a-plans-file-is-yyyy-mm-dd-slug-md.md)
- [No CI on a push for now](docs/rulings/no-ci-on-a-push-for-now.md)
- [The tests are to be useful and fast](docs/rulings/the-tests-are-to-be-useful-and-fast.md)
- [The plan talk stays as one plan, one reviewer and a closed list, and it can stop a task](docs/rulings/the-plan-talk-stays-as-one-plan-one-reviewer-and-a-closed-list-and-it-can-stop-a-task.md)
- [The tests are chosen by what can fail, and a task is quick.](docs/rulings/the-tests-are-chosen-by-what-can-fail-and-a-task-is-quick.md)
- [A plan may end with a documentation task](docs/rulings/a-plan-may-end-with-a-documentation-task.md)

### A decision without him: the ladder, the experts and the breaker

- [A builder's question about the outcome goes to the personas](docs/rulings/a-builders-question-about-the-outcome-goes-to-the-personas.md)
- [The owner learns at the end what was decided for him, each with a short why](docs/rulings/the-owner-learns-at-the-end-what-was-decided-for-him-each-with-a-short-why.md)
- [`/lem ask-expert` takes a question in words, or none](docs/rulings/lem-ask-expert-takes-a-question-in-words-or-none.md)
- [In doubt, a decision climbs a ladder of opinions, and a count decides, not a model.](docs/rulings/in-doubt-a-decision-climbs-a-ladder-of-opinions-and-a-count-decides-not-a-model.md)
- [The question gate stays, hidden, and may decide](docs/rulings/the-question-gate-stays-hidden-and-may-decide.md)
- [Without Codex one expert answers alone.](docs/rulings/without-codex-one-expert-answers-alone.md)
- [A choice that matters is logged, also when nobody was asked](docs/rulings/a-choice-that-matters-is-logged-also-when-nobody-was-asked.md)
- [The experts know the personas](docs/rulings/the-experts-know-the-personas.md)
- [A decision in the build goes to the personas first, and the build asks him nothing.](docs/rulings/a-decision-in-the-build-goes-to-the-personas-first-and-the-build-asks-him-nothing.md)
- [The build asks him nothing, and the ladder always decides](docs/rulings/the-build-asks-him-nothing-and-the-ladder-always-decides.md)
- [Only a circuit breaker stops a task, with a document](docs/rulings/only-a-circuit-breaker-stops-a-task-with-a-document.md)

### The review, the pull request and the merge

- [A review comes before the merge, and a task ends as a pull request.](docs/rulings/a-review-comes-before-the-merge-and-a-task-ends-as-a-pull-request.md)
- [A project can close branches](docs/rulings/a-project-can-close-branches.md)
- [A small defect outside the task is fixed at the end](docs/rulings/a-small-defect-outside-the-task-is-fixed-at-the-end.md)
- [After a merge, Lem repairs only a pull request with a conflict](docs/rulings/after-a-merge-lem-repairs-only-a-pull-request-with-a-conflict.md)
- [One way to merge in each project, and no prompt](docs/rulings/one-way-to-merge-in-each-project-and-no-prompt.md)
- [`branch.history` is `"squash"` by default](docs/rulings/branch-history-is-squash-by-default.md)
- [There is no train: the button on GitHub and `/lem land` are the same merge, and a task's branch is never merged by hand.](docs/rulings/there-is-no-train-the-button-on-github-and-lem-land-are-the-same-merge-and-a-tasks-branch-is-never-merged-by-hand.md)
- [A polish pass is a step of the flow](docs/rulings/a-polish-pass-is-a-step-of-the-flow.md)
- [A partial review is a review](docs/rulings/a-partial-review-is-a-review.md)
- [The review is routed by an agent that knows what each profile is for](docs/rulings/the-review-is-routed-by-an-agent-that-knows-what-each-profile-is-for.md)
- [Landings run in parallel, and the machine's load decides when checks start](docs/rulings/landings-run-in-parallel-and-the-machines-load-decides-when-checks-start.md)
- [A fresh merge agent reads every proposed task, and merges it or calls him](docs/rulings/a-fresh-merge-agent-reads-every-proposed-task-and-merges-it-or-calls-him.md)
- [GitHub pull requests are the one way to land](docs/rulings/github-pull-requests-are-the-one-way-to-land.md)

### A task's session, and whether he is there

- [A task runs with him or alone, and he can let go at any stage.](docs/rulings/a-task-runs-with-him-or-alone-and-he-can-let-go-at-any-stage.md)
- [He says whether he is there, and Lem assumes nothing](docs/rulings/he-says-whether-he-is-there-and-lem-assumes-nothing.md)
- [His away status is one mark of the machine, and a night task always runs without him](docs/rulings/his-away-status-is-one-mark-of-the-machine-and-a-night-task-always-runs-without-him.md)
- [No global Lem, and there is no Lem session.](docs/rulings/no-global-lem-and-there-is-no-lem-session.md)
- [A task's session is a fresh agent, with the talk copied in by `lem session talk`.](docs/rulings/a-tasks-session-is-a-fresh-agent-with-the-talk-copied-in-by-lem-session-talk.md)
- [Each task lives in a session of its own, from its shape to its merge, and there is no Lem session.](docs/rulings/each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session.md)
- [Inside a phase a session compacts itself at his number, for all his repositories.](docs/rulings/inside-a-phase-a-session-compacts-itself-at-his-number-for-all-his-repositories.md)

### The board and the pages for him

- [The monitor is required](docs/rulings/the-monitor-is-required.md)
- [Lem asks through its question page](docs/rulings/lem-asks-through-its-question-page.md)
- [A page for the owner has the board's look](docs/rulings/a-page-for-the-owner-has-the-boards-look.md)
- [The backlog is a part of Lem, and its view is a tab of the board](docs/rulings/the-backlog-is-a-part-of-lem-and-its-view-is-a-tab-of-the-board.md)
- [A board of example tasks says so on the page](docs/rulings/a-board-of-example-tasks-says-so-on-the-page.md)
- [The time card gets exact start times](docs/rulings/the-time-card-gets-exact-start-times.md)
- [What waits for the owner is one list, with a decision for each item](docs/rulings/what-waits-for-the-owner-is-one-list-with-a-decision-for-each-item.md)
- [A chord opens a list of the tasks](docs/rulings/a-chord-opens-a-list-of-the-tasks.md)
- [A page to read opens as a companion](docs/rulings/a-page-to-read-opens-as-a-companion.md)
- [What reaches across tasks is the board server's](docs/rulings/what-reaches-across-tasks-is-the-board-servers.md)
- [The board is a served app](docs/rulings/the-board-is-a-served-app.md)
- [The board's icons are a subset of Font Awesome Pro, in the repository, under his license](docs/rulings/the-boards-icons-are-a-subset-of-font-awesome-pro-in-the-repository-under-his-license.md)
- [Tailscale is the way from his phone, and nothing supervises the server](docs/rulings/tailscale-is-the-way-from-his-phone-and-nothing-supervises-the-server.md)
- [An address for each workspace and task, two machines under one, and pushes](docs/rulings/an-address-for-each-workspace-and-task-two-machines-under-one-and-pushes.md)
- [He acts from the board](docs/rulings/he-acts-from-the-board.md)
- [No stale pull request, and a folded header on a phone](docs/rulings/no-stale-pull-request-and-a-folded-header-on-a-phone.md)
- [Stories, flowcharts and pictures, early](docs/rulings/stories-flowcharts-and-pictures-early.md)
- [A task's artifacts have one map](docs/rulings/a-tasks-artifacts-have-one-map.md)

### The settings, the seats and the tracker

- [Linear and GitHub Issues, and the local backlog stays local](docs/rulings/linear-and-github-issues-and-the-local-backlog-stays-local.md)
- [A check of the tracker is no command of the owner's](docs/rulings/a-check-of-the-tracker-is-no-command-of-the-owners.md)
- [A seat is written `agent/model:effort`](docs/rulings/a-seat-is-written-agent-model-effort.md)
- [The state of Lem is not in the git directory](docs/rulings/the-state-of-lem-is-not-in-the-git-directory.md)
- [Not every section of the settings stays](docs/rulings/not-every-section-of-the-settings-stays.md)
- [The Linear table is short](docs/rulings/the-linear-table-is-short.md)
- [Each of the three seats is written whole](docs/rulings/each-of-the-three-seats-is-written-whole.md)
- [No setting counts the tasks that run. A night works its items one after another](docs/rulings/no-setting-counts-the-tasks-that-run-a-night-works-its-items-one-after-another.md)
- [`[checks]` keeps three keys, and `alone` is `serial`.](docs/rulings/checks-keeps-three-keys-and-alone-is-serial.md)
- [The topics are proposed at the setup](docs/rulings/the-topics-are-proposed-at-the-setup.md)
- [Four places are settings](docs/rulings/four-places-are-settings.md)
- [`[tracker]` has one key](docs/rulings/tracker-has-one-key.md)
- [`/lem read KEY` shows a ticket](docs/rulings/lem-read-key-shows-a-ticket.md)
- [The Done column shows the newest ended tasks, and one setting says how long an ended task's files stay](docs/rulings/the-done-column-shows-the-newest-ended-tasks-and-one-setting-says-how-long-an-ended-tasks-files-stay.md)

### The README, the guides and the logo

- [The logo is the owner's pick](docs/rulings/the-logo-is-the-owners-pick.md)
- [The README is in ASD-STE100 Simplified Technical English](docs/rulings/the-readme-is-in-asd-ste100-simplified-technical-english.md)
- [The README tells a command he types from one a job or Lem runs](docs/rulings/the-readme-tells-a-command-he-types-from-one-a-job-or-lem-runs.md)
- [The texts assume a public repository](docs/rulings/the-texts-assume-a-public-repository.md)
- [The README and the docs do not report what ran](docs/rulings/the-readme-and-the-docs-do-not-report-what-ran.md)
- [No history and no reasons in a text for a reader](docs/rulings/no-history-and-no-reasons-in-a-text-for-a-reader.md)
- [The README is easy for a reader who is not a native speaker](docs/rulings/the-readme-is-easy-for-a-reader-who-is-not-a-native-speaker.md)
- [Lem's docs do not speak for another tool](docs/rulings/lems-docs-do-not-speak-for-another-tool.md)
- [The README shows the interaction, and links to no run](docs/rulings/the-readme-shows-the-interaction-and-links-to-no-run.md)
- [The README says a plugin that works closely with agterm, and names no operating system](docs/rulings/the-readme-says-a-plugin-that-works-closely-with-agterm-and-names-no-operating-system.md)
- [Each label of a chart is quoted.](docs/rulings/each-label-of-a-chart-is-quoted.md)

### The lessons, the correction queue, the naps, the night and the free hour

- [The free hour may edit Lem's skills on a branch of the clone.](docs/rulings/the-free-hour-may-edit-lems-skills-on-a-branch-of-the-clone.md)
- [The correction hook is an optional part.](docs/rulings/the-correction-hook-is-an-optional-part.md)
- [As a plugin, the correction hook comes with the install, and the repository says yes for all](docs/rulings/as-a-plugin-the-correction-hook-comes-with-the-install-and-the-repository-says-yes-for-all.md)
- [Lem naps](docs/rulings/lem-naps.md)
- [The lessons, the retro and Jev stay; a night run ends as a pull request; naps are not shown](docs/rulings/the-lessons-the-retro-and-jev-stay-a-night-run-ends-as-a-pull-request-naps-are-not-shown.md)
- [The Jev model comes through any provider](docs/rulings/the-jev-model-comes-through-any-provider.md)
- [The naps are Lem's look back over its own memory](docs/rulings/the-naps-are-lems-look-back-over-its-own-memory.md)

## Decisions the maintaining session took

None of these is his ruling: each is a decision or a design of the session that maintains Lem,
and open to him. Each sentence is the text of a link to its file in `.lem/decisions/`.

### What Lem is, and who it is for

- [Lem is a companion, not a gate](.lem/decisions/lem-is-a-companion-not-a-gate.md)
- [Two rulings that say one rule are merged when one of them next changes, not before](.lem/decisions/two-rulings-that-say-one-rule-are-merged-when-one-of-them-next-changes-not-before.md)

### What Lem needs on the machine

- [Lem is a Claude Code plugin](.lem/decisions/lem-is-a-claude-code-plugin.md)

### A request: its type, its track and its commands

- [The session's answers to his notes that asked a question: `[gate]` is renamed `[checks]`, a lead queues a task behind another open task whose result it needs, and the plugin's commands carry Lem's name.](.lem/decisions/the-sessions-answers-to-his-notes-that-asked-a-question-gate-is-renamed-checks-a-lead-queues-a-task-behind-another-open-task-whose-result-it-needs-and-the-plugins-commands-carry-lems-name.md)
- [`/lem build` takes a plan file too, and lists the waiting plans when it gets no name](.lem/decisions/lem-build-takes-a-plan-file-too-and-lists-the-waiting-plans-when-it-gets-no-name.md)
- [Whether a change is careful is inferred from what the owner said must not go wrong, never matched from a list of paths](.lem/decisions/whether-a-change-is-careful-is-inferred-from-what-the-owner-said-must-not-go-wrong-never-matched-from-a-list-of-paths.md)
- [The size of a change decides its path](.lem/decisions/the-size-of-a-change-decides-its-path.md)
- [Every edit of the settings file is careful](.lem/decisions/every-edit-of-the-settings-file-is-careful.md)
- [An ask waits for another task when it needs that task's result, not when it names the same code](.lem/decisions/an-ask-waits-for-another-task-only-when-it-needs-that-tasks-result.md)

### The interview, the criteria and the personas

- [Where the stages keep what the amendment of 2026-11-16 says otherwise.](.lem/decisions/where-the-stages-keep-what-the-amendment-of-2026-11-16-says-otherwise.md)
- [A full change has one approval and no ceremony that nobody asked for](.lem/decisions/a-full-change-has-one-approval-and-no-ceremony-that-nobody-asked-for.md)

### The plan, the build and the tests

- [Lem brings its own builder agent](.lem/decisions/lem-brings-its-own-builder-agent.md)
- [A plan talk's record is taken as it ran.](.lem/decisions/a-plan-talks-record-is-taken-as-it-ran.md)
- [A plan never makes a change small](.lem/decisions/a-plan-never-makes-a-change-small.md)
- [The checks remove what their own commands leave](.lem/decisions/the-checks-remove-what-their-own-commands-leave.md)
- [Two builders of one plan that run at one moment commit only their own paths](.lem/decisions/two-builders-of-one-plan-that-run-at-one-moment-commit-only-their-own-paths.md)

### A decision without him: the ladder, the experts and the breaker

- [A decision of the plan does not hold the task: `held` keeps what has no options, the criteria that wait for his yes, one more fact for an investigation and a step that is his to do.](.lem/decisions/a-decision-of-the-plan-does-not-hold-the-task-held-keeps-what-has-no-options-the-criteria-that-wait-for-his-yes-one-more-fact-for-an-investigation-and-a-step-that-is-his-to-do.md)
- [The mode and the ladder are built in the smaller of two designs](.lem/decisions/the-mode-and-the-ladder-are-built-in-the-smaller-of-two-designs.md)
- [A machine failure stops a task as `blocked`, with one line that names what to do, and with no breaker's document](.lem/decisions/a-machine-failure-stops-a-task-as-blocked-with-one-line-that-names-what-to-do-and-with-no-breakers-document.md)

### The review, the pull request and the merge

- [A lowered bar (a new suppression, a skipped or deleted test, fewer assertions) makes a pull request not green also when the plan gives its reason.](.lem/decisions/a-lowered-bar-a-new-suppression-a-skipped-or-deleted-test-fewer-assertions-makes-a-pull-request-not-green-also-when-the-plan-gives-its-reason.md)
- [Lem lands Lem by a rule, not by machinery](.lem/decisions/lem-lands-lem-by-a-rule-not-by-machinery.md)
- [The status knows what merged](.lem/decisions/the-status-knows-what-merged.md)
- [A small change never gets a polish pass](.lem/decisions/a-small-change-never-gets-a-polish-pass.md)
- [The push and the pull request of `propose` need no question](.lem/decisions/the-push-and-the-pull-request-of-propose-need-no-question.md)
- [Two things a real run showed on 2026-11-18](.lem/decisions/two-things-a-real-run-showed-on-2026-11-18.md)
- [The board's server runs the merge agent's merge, and the agent only writes its review](.lem/decisions/the-boards-server-runs-the-merge-agents-merge-and-the-agent-only-writes-its-review.md)
- [Two reviews of the release, and what the session took](.lem/decisions/two-reviews-of-the-release-and-what-the-session-took.md)

### A task's session, and whether he is there

- [The copied talk stays in Lem's untracked state folder and never reaches git or a pull request.](.lem/decisions/the-copied-talk-stays-in-lems-untracked-state-folder-and-never-reaches-git-or-a-pull-request.md)
- [A task that ended stays ended](.lem/decisions/a-task-that-ended-stays-ended.md)
- [The trials of 2026-11-21: a task's session takes the focus only for its own question and says its first line first, and the onboarding writes no allow rules and commits the plugin's file](.lem/decisions/the-trials-of-2026-11-21-a-tasks-session-takes-the-focus-only-for-its-own-question-and-says-its-first-line-first-and-the-onboarding-writes-no-allow-rules-and-commits-the-plugins-file.md)
- [The first line of a task is composed by `lem project state`, and its session says it as it is](.lem/decisions/the-first-line-of-a-task-is-composed-by-lem-project-state-and-its-session-says-it-as-it-is.md)

### The board and the pages for him

- [The board is served, and the server draws it](.lem/decisions/the-board-is-served-and-the-server-draws-it.md)

### The settings, the seats and the tracker

- [The reviewer's seat is written `agent/model:effort`.](.lem/decisions/the-reviewers-seat-is-written-agent-model-effort.md)
- [One machine may name its own reviewer for a while](.lem/decisions/one-machine-may-name-its-own-reviewer-for-a-while.md)
- [Onboarding asks three questions](.lem/decisions/onboarding-asks-three-questions.md)

### The README, the guides and the logo

- [The texts people read say "the owner"](.lem/decisions/the-texts-people-read-say-the-owner.md)

### The lessons, the correction queue, the naps, the night and the free hour

- [One person can say no to the correction queue, and nobody is switched on by a file git does not show](.lem/decisions/one-person-can-say-no-to-the-correction-queue-and-nobody-is-switched-on-by-a-file-git-does-not-show.md)
- [No project's session edits Lem](.lem/decisions/no-projects-session-edits-lem.md)
- [A correction hook registered twice judges each message once](.lem/decisions/a-correction-hook-registered-twice-judges-each-message-once.md)
- [A night ends as pull requests, and a task without the owner covers what a night was](.lem/decisions/a-night-ends-as-pull-requests-and-a-task-without-the-owner-covers-what-a-night-was.md)

## Checks

```bash
bash tests/all.sh              # every suite below at the same time, one log each, a line of ok, FAIL and SKIP per suite
python3 tests/pick.py --base main  # the suites to run for what the branch changed (or name the files); all.sh still runs before main moves
python3 -B -m unittest discover -s tests/unit  # the unit level: one file for each script, its rules called in one process; all.sh runs it as the suite unit
```

The loop: the unit level after each edit; while a task is in work, only the one block that holds
the journey it changes; the blocks that `tests/pick.py` names once for a task, at its end;
`tests/all.sh` once before `main` moves. A block is never run before a change to count it: the
counts of the last full run are the before. A rule that takes facts and returns a result is a
unit case, a call of its function; a fact only git can show is a check in a block, in a throwaway
repository.

Each suite says how many checks it holds (`collected N`, `tests/checks.sh`), and a check that
cannot run here prints a `SKIP` line of its own. A suite whose `ok` and `SKIP` lines do not add up
to that count fails, and so does one that runs over its time limit (`LEM_TEST_LIMIT`, 30 minutes).
With `LEM_TEST_TIMES=FILE` each check of a block appends its seconds to FILE, so one run shows
which checks hold the time.

One suite alone, in the order of `tests/all.sh`:

```bash
bash tests/lem-settings.sh     # the settings and the places of what Lem reads, a task's state and the event log, the rule picker, the criteria and their check on the base (each lem-* block sources tests/lib.sh)
bash tests/lem-machine.sh      # the machine check, the correction queue and its hook, the plugin's files
bash tests/lem-state.sh        # the state folder git never sees, and the owner's status
bash tests/lem-decisions.sh    # a task's decisions, each taken by a level of the ladder, and the circuit breaker from its trip to his help, park, drop and resume
bash tests/lem-land-shop.sh    # the landing from `ready` through the checks and one read to a pull request, the merge agent's read and the merge, on the stand-in for gh
bash tests/lem-land-local.sh   # the landing in two halves of about equal time: decisions, criteria and the personas' read in the pull request's text here,
bash tests/lem-land-review.sh  # and the polish pass, the review, the bar, what makes a request careful and who merges it here
bash tests/lem-land-backlog.sh # what a review saw outside the change, filed as backlog items
bash tests/lem-land-github.sh  # the forge's own cases, and a remote that is not GitHub, which lands nothing
bash tests/lem-land-guards.sh  # the landing's guards and refusals, each next step run as the refusal names it
bash tests/lem-land-small.sh   # the fast track's landing, and what keeps it safe
bash tests/lem-serial.sh       # checks.serial under the repository's one lock, and checks.setup in a new worktree
bash tests/lem-naps.sh         # the [naps] settings and lem project may-nap
bash tests/lem-command.sh      # the command lem: each name, its arguments, stdin and exit status, help, and that no text names a script by its path
bash tests/lem-picker.sh       # the task picker, with a stand-in for agtermctl
bash tests/lem-session.sh      # a task's own session (lem session) with a stand-in for agtermctl, and the copy of the talk
bash tests/lem-serve.sh        # the board server and lem board over HTTP, on the afternoon of tests/board-showcase.py: the routes, each page's words, the stream, the jump to a session, the start on demand
bash tests/lem-board-act.sh    # the owner's acts from the board, and the server's duties across tasks, with a stand-in for lem session
bash tests/lem-peers.sh        # two machines under one address: two board servers on this Mac, a join, the loop guard, a machine that does not answer
bash tests/test-gate-panel.sh  # the panel's cast, in its one place
bash tests/test-ask.sh         # lem-ask's spec checks and every template; loads pages in headless Chrome when one is installed
bash tests/test-ask-expert.sh  # the experts' brief of a question in words, its folder and the record of each answer, one expert alone; no expert runs
bash tests/test-site.sh        # the page on GitHub Pages, from pages.yml's own copy step; its drawn page in headless Chrome when one is installed
bash tests/shellcheck.sh       # ShellCheck over tests/*.sh, one check for each file, or over the files named
python3 tests/pick.py --check  # the map of tests/pick.py: every file read by a suite, every suite in all.sh
bash tests/test-lem.sh         # every lem-* block at the same time, with its output in order; all.sh runs each as a suite of its own
```

A change to a script comes with its test. A change to a stage file has no test: its test is a
real task, so say in the commit which task showed the need.

To run a clone of Lem in one session, without the plugin's install, load its folder as the plugin
(Claude Code 2.1.325, 2026-11-17: the session listed every `lem:` skill and `lem:lem-builder`):

```bash
claude --plugin-dir /path/to/lem   # the plugin from this folder, for this session only, with its skills, agent, commands and hooks
```

A task's session that `lem session open` starts gets `--plugin-dir` with the clone's folder when
no Lem is installed (`plugin_dir` in `session.py`). With an older Lem installed for the project, the
`lem` on that session's `PATH` is still the installed one (lem-scratch, Claude Code 2.1.330,
2026-11-21): a real task is tried with the release installed.

## Layout

Each script's module docstring says what it does and why; this list says where each thing is.

- `skills/lem/SKILL.md`: the entry point, what holds in every stage, and "One session for each
  task".
- `skills/lem/stages/`: one file for each subcommand, read only when it runs. `new.md` opens a task
  in its own session, and its "The request" and "The fast track" are that session's first steps;
  `interview.md` (the interview and the criteria) and `investigate.md` (a bug, a question) are the
  rest of the shape. `start.md` starts the build, `plan.md` and `build.md` are the lead's, `talk.md`
  is the plan talk, which only its defender reads, `ladder.md` a decision in doubt and `breaker.md`
  the circuit breaker. `land.md` is the land phase, `polish.md` its step 3, on the standard
  track only, and `conflict.md` what an open pull request takes when GitHub calls it conflicting.
  `status.md`, `away.md`, `correct.md`, `park.md`, `night.md`, `init.md`, `learn.md`
  and `nap.md` are the owner's other commands and the scheduled ones.
- `skills/lem/prompts/`: the standing briefs: `session.md` (a task's session: what it reads, a
  change of phase, a wake-up, what it never does), `lead.md`, `defender.md` and `reviewer.md` (the
  plan talk's pair), `scout.md`, `investigator.md`, `small.md` (the fast track's one builder),
  `landing.md` (a builder of a landing), `review.md` (the review before a pull request), `merge.md`
  (the merge agent), `writing.md` (how a document for the owner is written, from the interview to
  the merge agent) and `nap.md`.
- `skills/lem/templates/`: `profile.md` and `persona.md`, which onboarding fills; `handoff.md`, the
  hand-over between two agents of a task; `breaker.md`, the breaker's document.
- `skills/lem/harness/`: the capability contract, `README.md`, and one file for each agent, a core with
  its parts in a folder of the agent's name (`claude-code/`).
- `skills/lem/scripts/`, each a command of `lem` or a module the commands share:
  - `project.py` (`lem project`): a repository's settings and the one place of each file Lem reads
    beside them (`PLACES`), a task's state and directory, the event log, the owner's status and its
    watch, `waiting` (the one list of what waits for the owner), `prune` (what the state folder
    keeps, `state.keep_days`, which one machine's `.lem/project.local.toml` may set for itself), and
    the machine's `load` and `handoff` numbers.
  - `session.py` (`lem session`): a task's own session in agterm, its change of phase, its wake-up,
    the handoff's check and the copy of the talk; `session_hook.py`: the plugin's `PreCompact` and
    `SessionStart` hooks of a task's session (every source: the record of each Claude Code session of
    the task, and after a compaction the task's files); `lem_tokens.py`: the tokens a task's Claude
    Code sessions spent, from their transcripts, for the merge brief.
  - `land.py` (`lem land`): the landing, one refusable step at a time, from `ready` through the
    checks and the review to a pull request on GitHub, the merge agent's read, the merge and the
    cleanup.
  - `criteria.py` (`lem criteria`): a task's acceptance criteria, and the check that each one's
    tests pass on the branch and fail on the base. `decisions.py` (`lem decisions`): a task's
    decisions, each taken without the owner, and its breakers.
  - `serve.py` (`lem serve`): the machine's one board server, with the owner's acts, the jump to a
    session, the tailnet door and the duties across tasks, the hourly `lem project prune` of each
    workspace among them; `serve_hook.py`: the SessionStart hook
    that starts it. Its parts: `lem_board_model.py` (the model, pure functions over the files),
    `lem_board_pages.py` (the pages of a workspace), `lem_board_task.py` (the board of one task),
    `lem_artifacts.py` (a task's files on one map), `lem_html.py` (`h()`, which escapes every text),
    `lem_push.py` (the notifications) and `lem_peers.py` (another machine joined with `--join`).
  - `board.py` (`lem board`): makes sure the server runs and opens a board, or with `--page FILE`
    any page of Lem, as a companion. `picker.py` (`lem picker`): agterm's picker over the tasks.
  - `doctor.py` (`lem doctor`): the machine check. `corrections.py` (`lem corrections`): the
    optional queue of the owner's corrections and its hook. `jev.py` (`lem-jev`): the client of the
    Jev model.
  - `lem_state.py` (the state folder and Lem's home folder), `lem_plans.py` (a plan's and a ruling's
    file name), `lem_sibling.py` (a sibling's command in the same process) and `lem_python.py` (a
    Python of 3.11 or newer for `bin/lem` and the hooks).
- `skills/lem/assets/`: what `lem serve` sends under `/assets/`. `board.css` is the board's look,
  the phone's too; `lem.css` and `lem.js` are the look and the palette every page of Lem shares, and
  a new page for the owner links both and brings no style of its own. `push.css` and `sw.js` are the
  notifications', `icons/` the board's icons, and `handover.html` the pattern of the onboarding's
  page. `vendor/` holds what `tools/board-kit` builds: `board-app.js`, the board's one script,
  `board-icons.json` and `mermaid.min.js`.
- `tools/board-kit/`: the maintainer's build of `vendor/`, which nobody who installs the plugin
  runs: the built files are committed. Its `README.md` says how to build and how to add a Stimulus
  controller to `controllers/`.
- Lem's home folder, `$XDG_CONFIG_HOME/lem` or `~/.config/lem` (`lem_state.config()`):
  `owner.jsonl`, the owner's away and back; `machine.toml`, this machine's settings, `[load]`,
  `[serve]`, `[peers]`, `[seats]` (`merger` and `session`, for a repository whose settings name
  none) and `[handoff]`; `workspaces.json`, the repositories the server shows; and what the server
  and the checks keep there: `serve.lock`, `serve.log`, `load.lock`, the push key `push-key.pem` and
  the devices `push.json`.
- `.lem/`: Lem's own settings, profile, cast and lessons, in the places every repository has them.
  Its `decisions/` holds the maintaining session's decisions and designs, one file for each, each
  linked by its sentence in "Decisions the maintaining session took", and a replaced one marked and
  linked by what replaced it. Its `state/`, which git ignores, is the state of a repository's Lem: the tasks, the event log,
  the night reports, the naps, the experts' folders, a panel's copies, the panels' folders
  (`panels/`, which `lem cast run-dir` makes), and `forge.json`, the board
  server's last look at GitHub. `lem project prune` removes from it what is older than
  `state.keep_days`. `.lem/worktrees/` holds
  the tasks' worktrees. `.revmux/` is the review tool's configuration for this repository.
- The naps, an optional part: `prompts/nap.md` is written after the owner's own nap routine and
  keeps its voice (a change is tried with one real nap, and its dream is read: a brief that makes a
  report of it is wrong); `stages/nap.md` starts one and `lem project may-nap` says whether one
  may. No page shows them; the retro reads their waking notes.
- `docs/`: the guides the README links, each in STE like the README, each with one job and under
  800 words: `flow.md` (how a task goes, with the one diagram), `when-lem-needs-you.md`,
  `pull-request.md` (what green means, the merge review, the merge, a conflict), `board.md` (the
  board, the phone, two machines under one address, the server), `install.md` and `linear.md`; and
  `settings.md`, the reference, one table for each table of the settings, one to one with
  `project.py` (`tests/lem-settings.sh` checks it). How Lem works inside is in this file and the
  skill. Beside them: `free-hour.md` (how an unattended maintainer's session may change Lem),
  `rulings/`, the owner's rulings, one file for each ruling in force, linked by its sentence in
  "The owner's rulings", with the rulings it replaced inside it, `backlog/`, Lem's own deferred work, and `plans/`, the plans that built Lem, each finished one
  with a status line that names its commits and where later decisions changed it; the redesign of
  2026-11-20 is `plans/2026-11-20-a-session-for-each-task.md` and its folder.
- `tests/`: the suites of "Checks". `unit/` is the unit level, a `test_*.py` for each script;
  `lib.sh` is what each `lem-*.sh` block sources, `checks.sh` how every suite counts its checks,
  `suites.sh` and `limit.py` what `all.sh` and `test-lem.sh` share, and `pick.py` the map of which
  suite reads which file. `board-showcase.py` writes the demo afternoon that `lem-serve.sh` serves,
  and makes the board's pictures through headless Chrome (`board-cdp.mjs`, which needs Node).
  `.github/workflows/ci.yml` runs `all.sh` when someone starts it by hand.
- `.claude-plugin/`, `bin/` and `hooks/`: what Claude Code reads to load this repository as the
  plugin `lem`, the one way Lem installs. `bin/lem` is Lem's one command: `lem NAME` runs the script
  NAME stands for, and `lem help` lists them; `lem-ask` and `lem-jev` are links to it.
  `hooks/hooks.json` starts, each through `lem_python.py`, the correction hook, the SessionStart
  hook of the board server and the two hooks of a task's session. Every text and every message of a
  script says `lem NAME`, so one permission rule, `Bash(lem *)`, covers them on every machine and
  after every update.
- `agents/lem-builder.md`: the builder, as a Claude Code agent definition; its body is the builder's
  standing rules, and `harness/claude-code.md` says how it is used and overridden.
- `assets/`: the logo (`lem.svg`), the figure alone (`lem-mark.svg`), and both in the night palette
  (`*-night.svg`, written by `night.py`). `assets/screens/` holds the board's pictures, light and
  dark, made by `tests/board-showcase.py`: `board-*` (the kanban), `task-*` (a task on "Overview"),
  `backlog-*` and `phone-*`. The README shows `board-*` and `phone-*`, `docs/board.md` `phone-*`,
  `docs/when-lem-needs-you.md` `task-*`, the site all three, and no page `backlog-*`.
- `site/`: Lem's page on GitHub Pages, `index.html` and `style.css`, written from the README and the
  guides in their STE, in the board's look (the six hues of `lem.css` at the same values), light or
  dark by the visitor's theme, with the copy buttons as its one script and nothing from another
  host. `.github/workflows/pages.yml`, started by hand only, copies it with the logo, the figure
  alone (the tab icon) and the six pictures into `_site/` at their repository paths and publishes
  that; `tests/test-site.sh` runs that copy step as written.
- `skills/lem-ask/`, `skills/lem-interview-me/`, `skills/lem-dialectic/`, `skills/lem-root-cause/`,
  `skills/lem-gate/`, `skills/lem-panel/`, `skills/lem-linear/`, `skills/lem-ask-expert/`: the
  skills Lem names and ships. `lem-ask-expert` is Lem's own, with `scripts/experts.py` (`lem
  experts`: the brief of a question in words and the record of the experts' answers, in a folder of
  `.lem/state/experts/`). `lem-panel`'s `scripts/cast.py` (`lem cast`) finds the cast, copies it
  into a project, keeps the copies a panel read in Lem's state folder, and makes each panel's own
  folder there, in `.lem/state/panels/`. `NOTICE` says where each
  came from.

## The shipped skills are copies, not yet under the rules above

Each was copied from where it worked and changed only as far as the new layout needed. Their text
still names Claude Code's tools,
and lem-ask's Stop hook (`skills/lem-ask/hooks/hooks.json`) is registered by nothing. Bring one under
the capability rule when a second agent has to run it, not before.

The set is deliberately small. A tool with its own life (revmux, agterm, the mailbox chat, webrev,
agdoc, the backlog recipe, cronn, plannotator-tui, Codex) is checked for by `doctor.py` and never
copied in. The backlog's item format is the recipe's, and Lem's builders read it in rule 6 of
`agents/lem-builder.md`; no builder loads the recipe's skill, which is the owner's own tool.

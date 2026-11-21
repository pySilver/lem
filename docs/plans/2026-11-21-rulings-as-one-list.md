# The rulings as one list

> **Status: built** on the branch `docs/rulings-as-one-list`, for the owner to read before it lands.
> The table below is what he reads: one row for each file that left.

## His words

On 2026-11-21, on a question page, after he had said three times that the number of files in
`docs/rulings/` (130) and `.lem/decisions/` (41) confused him:

- To "What must docs/rulings hold?" he chose "One plain list of the 59 principles" and wrote: "It
  feel like rulings should be a single file with bullet list, where each item eventually allows
  minimal description. This way it will not drift".
- To "What must .lem/decisions hold?" he chose "The 5 principles join the plain list, and the folder
  goes" and wrote: "Just like in rulings - a single file might be a good idea."
- Earlier the same day: "We can eventually condense it to some plain list of rules?"

A ruling leaves only on his word. He gave it for the form; for each file he reads the table below
and may move it back.

## What was done

- `docs/rulings/rulings.md` is the list: one bullet for each ruling of his in force, under the
  twelve groups `AGENTS.md` had, and in its last part, "Choices of the maintaining session", the
  choices of the session that are open to him. A ruling that only said what another says, or a part
  of it, gave its words to that one's bullet.
- `docs/rulings/history.md` holds what left the list, each line with what keeps it now: a test
  (`tests/unit/test_agents_md.py` fails when that test is renamed or removed), or one place in the
  code or a text. Where the place did not say the rule yet, one line was added there: in `AGENTS.md`
  (the plugin's names, the owner's name in a script's text, the quotes of a chart, a journey run
  once) and in `skills/lem/SKILL.md` (the row `blocked`).
- The 171 files left in one commit, and the folder of the session's decisions is gone. `AGENTS.md`
  names the two files and says when an agent reads them, and its rules for a ruling are the rules
  of the list.
- A file a classifier had put in the history came back to the list when its test held only a part
  of it (three choices of the session), when its place did not hold it ("The Done column shows the
  newest ended tasks", whose limit is not built; "The first run is in a scratch repository"), or
  when its words disagree with another bullet's ("Stories, flowcharts and pictures, early" against
  "One approved line of a task is an acceptance criterion", which says no text says story; both
  stand as written, for him to settle).
- A second agent read the list against the 171 files. What it found is corrected: two bent
  meanings, the rules a bullet had lost, and five bullets where the session's form stood as his
  ruling. That form left a bullet where the code or the history holds it, and is marked "(the form
  is the session's)" where the bullet needs it.

## How to move a file back

Name its row: "move back STEM". The session then takes its text from git (`git show
04ba08c:docs/rulings/STEM.md`, or the same path in the folder of the session's decisions), writes
it as a bullet of the list in its group, removes its line from the history where it has one, and
writes "yes" in the last column of its row.

## The table

The rows of the list come first, in the list's order; then the history's rows held by a test, then
those kept in one place, then the two that left with nothing. "Class" is the classifier's: P a
principle or a boundary, E held by a check, D a detail with one place, M the same rule as another
ruling (its carrier), S mostly changed by later rulings; "now" says where this change put a file
against its class.

| Folder | File | Class | Where its text went | Moved back |
| --- | --- | --- | --- | --- |
| `docs/rulings` | `lem-is-for-experienced-developers-and-every-change-is-measured-against-that` | P | the list: "Lem is for experienced developers, and every change is measured against that." | no |
| `docs/rulings` | `the-user-of-lem-is-a-senior-developer-with-little-attention-to-give` | M | the list, in the bullet "Lem is for experienced developers, and every change is measured against that." (its user, a senior developer with little attention to give, never a business reader; and its own bullet "What he names in the interview is a direction the plan follows") | no |
| `docs/rulings` | `one-lem-for-one-repository` | P | the list: "One Lem for one repository." | no |
| `docs/rulings` | `no-global-lem-and-there-is-no-lem-session` | M | the list, in the bullet "One Lem for one repository." (no global Lem; "there is no Lem session" is in the bullet of each task's session) | no |
| `docs/rulings` | `claude-code-and-agterm-first-and-codex-for-reviews` | P | the list: "Claude Code and agterm first, and Codex for reviews." | no |
| `docs/rulings` | `claude-code-first` | M | the list, in the bullet "Claude Code and agterm first, and Codex for reviews." (the reviewer may be Codex or a second Claude; the harness file for Codex comes later) | no |
| `docs/rulings` | `opinionated-and-small` | P | the list: "Opinionated and small." | no |
| `docs/rulings` | `the-rules-of-an-existing-project-stay-where-they-are` | P | the list: "The rules of an existing project stay where they are." | no |
| `docs/rulings` | `another-programs-settings-stay-where-that-program-keeps-them` | P | the list: "Another program's settings stay where that program keeps them." | no |
| `docs/rulings` | `three-more-commands-are-no-commands-of-his-and-two-recipes-of-the-agterm-cookbook-become-required` | P | the list: "Three more commands are no commands of his, and two recipes of the agterm cookbook become required." | no |
| `docs/rulings` | `webrev-is-the-way-to-mark-up-a-plan-or-a-document-a-required-recipe-of-the-agterm-cookbook-and-it-is-not-a-part-of-lem` | S | the list, in the bullet "Three more commands are no commands of his, and two recipes of the agterm cookbook become required." (`/webrev` marks up a plan or a document, none of the tools is copied into Lem; agdoc and plannotator-tui are recommended in the bullet "agterm, the mailbox chat and revmux stay required") | no |
| `docs/rulings` | `lem-is-a-plugin-and-nothing-else` | P | the list: "Lem is a plugin, and nothing else." | no |
| `.lem/decisions` | `lem-is-a-claude-code-plugin` | M | the list, in the bullet "Lem is a plugin, and nothing else." (the plugin's files are named in `AGENTS.md`, "Layout") | no |
| `docs/rulings` | `lem-is-his-one-desk-for-work-in-a-repository-and-its-core-is-the-path-from-a-request-to-a-merged-pull-request` | P | the list: "Lem is his one desk for work in a repository, and its core is the path from a request to a merged pull request." | no |
| `docs/rulings` | `release-last-tag-and-the-review-of-another-persons-pull-request-leave-the-core` | P | the list: "Release, last-tag and the review of another person's pull request leave the core." | no |
| `docs/rulings` | `no-word-and-no-form-of-a-lem-before-is-kept` | P | the list: "No word and no form of a Lem before is kept." | no |
| `docs/rulings` | `the-shipped-skills-are-for-the-times-he-steps-in` | P | the list: "The shipped skills are for the times he steps in." | no |
| `docs/rulings` | `agterm-the-mailbox-chat-and-revmux-stay-required` | P | the list: "agterm, the mailbox chat and revmux stay required." | no |
| `docs/rulings` | `agterm-is-a-hard-dependency` | M | the list, in the bullet "agterm, the mailbox chat and revmux stay required." (Lem does not run outside agterm) | no |
| `docs/rulings` | `cronn-is-required-and-codex-is-highly-recommended` | P | the list: "cronn is required, and Codex is highly recommended." | no |
| `docs/rulings` | `lem-assumes-auto-mode` | P | the list: "Lem assumes auto mode." | no |
| `docs/rulings` | `python-3-11-stays-in-the-modern-form` | P | the list: "Python 3.11 stays, in the modern form." | no |
| `docs/rulings` | `what-must-not-go-wrong-is-named-by-topic-and-an-agent-says-whether-a-task-is-careful` | P | the list: "What must not go wrong is named by topic, and an agent says whether a task is careful." | no |
| `docs/rulings` | `the-topics-are-proposed-at-the-setup` | M | the list, in the bullet "What must not go wrong is named by topic, and an agent says whether a task is careful." (`/lem init` proposes the topics from the code) | no |
| `docs/rulings` | `lem-tells-the-type-of-a-request-asks-when-it-is-unclear-and-a-bug-is-investigated-first` | P | the list: "Lem tells the type of a request, asks when it is unclear, and a bug is investigated first." (its form is marked the session's; the fresh builder of a bug is in `skills/lem/stages/new.md`) | no |
| `docs/rulings` | `the-first-line-is-where-he-corrects-lems-read-of-a-request` | P | the list: "The first line is where he corrects Lem's read of a request." | no |
| `docs/rulings` | `the-two-tracks-are-the-fast-track-and-the-standard-track` | P | the list: "The two tracks are the fast track and the standard track." | no |
| `docs/rulings` | `a-helper-starts-from-plain-words` | P | the list: "A helper starts from plain words." | no |
| `docs/rulings` | `a-task-order-in-his-words-stays` | P | the list: "A task order in his words stays." | no |
| `docs/rulings` | `the-personas-read-of-the-acceptance-criteria-is-his-to-skip-and-only-when-every-criterion-names-only-the-developer` | P | the list: "The personas' read of the acceptance criteria is his to skip, and only when every criterion names only the developer." | no |
| `docs/rulings` | `every-project-of-lem-has-personas-and-a-panel-asks-the-projects-own` | P | the list: "Every project of Lem has personas, and a panel asks the project's own." | no |
| `docs/rulings` | `one-approved-line-of-a-task-is-an-acceptance-criterion` | P | the list: "One approved line of a task is an acceptance criterion." (its "none says story" disagrees with "Stories, flowcharts and pictures, early"; both stand as written) | no |
| `docs/rulings` | `a-complete-ticket-that-someone-else-wrote-needs-his-yes-to-its-criteria-and-no-interview` | P | the list: "A complete ticket that someone else wrote needs his yes to its criteria, and no interview." | no |
| `docs/rulings` | `most-requests-have-an-interview-and-his-check-of-the-acceptance-criteria-and-the-pull-request-says-green-or-not-green-first` | P | the list: "Most requests have an interview and his check of the acceptance criteria, and the pull request says green or not green first." | no |
| `docs/rulings` | `the-personas-read-first-and-their-confusion-may-change-the-design` | P | the list: "The personas read first, and their confusion may change the design." | no |
| `docs/rulings` | `the-first-run-is-in-a-scratch-repository` | D, now list | the list: "The first run is in a scratch repository, then in a real project." (D with no place: a one-time order, carried out) | no |
| `docs/rulings` | `each-task-of-a-plan-gets-a-fresh-builder` | P | the list: "Each task of a plan gets a fresh builder." | no |
| `docs/rulings` | `the-plan-talk-is-a-pair-in-a-companion-that-closes-after-it` | P | the list: "The plan talk is a pair in a companion that closes after it, and it can stop a task." (a doubt of the classifier: close to S) | no |
| `docs/rulings` | `the-plan-talk-stays-as-one-plan-one-reviewer-and-a-closed-list-and-it-can-stop-a-task` | M | the list, in the bullet "The plan talk is a pair in a companion that closes after it, and it can stop a task." (one plan, one reviewer, a closed list, not task by task; it stops a task only by the circuit breaker) | no |
| `docs/rulings` | `the-owner-learns-at-the-end-what-was-decided-for-him-each-with-a-short-why` | P | the list: "The owner learns at the end what was decided for him, each with a short why." | no |
| `docs/rulings` | `in-doubt-a-decision-climbs-a-ladder-of-opinions-and-a-count-decides-not-a-model` | P | the list: "In doubt, a decision climbs a ladder of opinions, and a count decides, not a model." | no |
| `docs/rulings` | `a-builders-question-about-the-outcome-goes-to-the-personas` | M | the list, in the bullet "In doubt, a decision climbs a ladder of opinions, and a count decides, not a model." (a builder's question about the outcome goes to the personas, not to the reviewer) | no |
| `docs/rulings` | `the-question-gate-stays-hidden-and-may-decide` | P | the list: "The question gate stays, hidden, and may decide." | no |
| `docs/rulings` | `the-build-asks-him-nothing-and-the-ladder-always-decides` | P | the list: "The build asks him nothing, and the ladder always decides." | no |
| `docs/rulings` | `a-decision-in-the-build-goes-to-the-personas-first-and-the-build-asks-him-nothing` | M | the list, in the bullet "The build asks him nothing, and the ladder always decides." (a decision in the build goes to the personas first) | no |
| `docs/rulings` | `only-a-circuit-breaker-stops-a-task-with-a-document` | P | the list: "Only a circuit breaker stops a task, with a document." (reads against `blocked`: see "A machine failure stops a task as `blocked`" in the history) | no |
| `docs/rulings` | `a-review-comes-before-the-merge-and-a-task-ends-as-a-pull-request` | P | the list: "A review comes before the merge, and a task ends as a pull request." | no |
| `docs/rulings` | `a-small-defect-outside-the-task-is-fixed-at-the-end` | P | the list: "A small defect outside the task is fixed at the end." | no |
| `docs/rulings` | `the-review-is-routed-by-an-agent-that-knows-what-each-profile-is-for` | P | the list: "The review is routed by an agent that knows what each profile is for." | no |
| `docs/rulings` | `landings-run-in-parallel-and-the-machines-load-decides-when-checks-start` | P | the list: "Landings run in parallel, and the machine's load decides when checks start." | no |
| `docs/rulings` | `a-fresh-merge-agent-reads-every-proposed-task-and-merges-it-or-calls-him` | P | the list: "A fresh merge agent reads every proposed task, and merges it or calls him." | no |
| `docs/rulings` | `github-pull-requests-are-the-one-way-to-land` | P | the list: "GitHub pull requests are the one way to land." | no |
| `docs/rulings` | `there-is-no-train-the-button-on-github-and-lem-land-are-the-same-merge-and-a-tasks-branch-is-never-merged-by-hand` | M | the list, in the bullet "GitHub pull requests are the one way to land." (the button on GitHub and `/lem land` are the same merge, a task's branch is never merged by hand) | no |
| `docs/rulings` | `one-way-to-merge-in-each-project-and-no-prompt` | S | the list, in the bullet "GitHub pull requests are the one way to land." (S: what is left, no prompt at a merge) | no |
| `docs/rulings` | `a-task-runs-with-him-or-alone-and-he-can-let-go-at-any-stage` | S | the list: "A task runs with him or alone, and he can let go at any stage." (S: what is left is its own bullet) | no |
| `docs/rulings` | `he-says-whether-he-is-there-and-lem-assumes-nothing` | P | the list: "He says whether he is there, and Lem assumes nothing." | no |
| `docs/rulings` | `each-task-lives-in-a-session-of-its-own-from-its-shape-to-its-merge-and-there-is-no-lem-session` | P | the list: "Each task lives in a session of its own, from its shape to its merge, and there is no Lem session." | no |
| `docs/rulings` | `a-tasks-session-is-a-fresh-agent-with-the-talk-copied-in-by-lem-session-talk` | M | the list, in the bullet "Each task lives in a session of its own, from its shape to its merge, and there is no Lem session." (the first agent gets the talk copied in by `lem session talk`) | no |
| `docs/rulings` | `the-monitor-is-required` | P | the list: "The monitor is required." | no |
| `docs/rulings` | `lem-asks-through-its-question-page` | S | the list: "Lem asks through its question page." (S: what is left is its own bullet) | no |
| `docs/rulings` | `a-page-for-the-owner-has-the-boards-look` | P | the list: "A page for the owner has the board's look." | no |
| `docs/rulings` | `what-reaches-across-tasks-is-the-board-servers` | P | the list: "What reaches across tasks is the board server's." (its merge of the merge agent's verdict is the session's, in the history's line "The board's server runs the merge agent's merge") | no |
| `docs/rulings` | `the-board-is-a-served-app` | P | the list: "The board is a served app." | no |
| `docs/rulings` | `the-boards-icons-are-a-subset-of-font-awesome-pro-in-the-repository-under-his-license` | P | the list: "The board's icons are a subset of Font Awesome Pro, in the repository, under his license." | no |
| `docs/rulings` | `tailscale-is-the-way-from-his-phone-and-nothing-supervises-the-server` | P | the list: "Tailscale is the way from his phone, and nothing supervises the server." | no |
| `docs/rulings` | `stories-flowcharts-and-pictures-early` | D, now list | the list: "Stories, flowcharts and pictures, early." (D, kept in the list: its "stories" disagrees with "One approved line of a task is an acceptance criterion") | no |
| `docs/rulings` | `linear-and-github-issues-and-the-local-backlog-stays-local` | P | the list: "Linear and GitHub Issues, and the local backlog stays local." | no |
| `docs/rulings` | `no-setting-counts-the-tasks-that-run-a-night-works-its-items-one-after-another` | P | the list: "No setting counts the tasks that run. A night works its items one after another." (a doubt of the classifier: between P and E) | no |
| `docs/rulings` | `the-done-column-shows-the-newest-ended-tasks-and-one-setting-says-how-long-an-ended-tasks-files-stay` | D, now list | the list: "The Done column shows the newest ended tasks, and one setting says how long an ended task's files stay." (D, back in the list: the Done column's limit is not built (`docs/backlog/the-board-s-done-column-has-no-limit.md`); the name `state.keep_days` is the session's form, in `docs/settings.md`) | no |
| `docs/rulings` | `tracker-has-one-key` | E, now list | the list: "`[tracker]` has one key." (E, kept in the list as a doubt of the classifier; `tests/unit/test_settings.py::Tracker.test_the_tables_it_takes` and `Tracker.test_a_key_that_went_is_unknown` hold it, so on his word it may move to the history) | no |
| `docs/rulings` | `the-linear-table-is-short` | M | the list, in the bullet "`[tracker]` has one key." (the team from the ticket's id, the statuses by their type, a failed connection points to Linear's MCP help page) | no |
| `docs/rulings` | `the-logo-is-the-owners-pick` | P | the list: "The logo is the owner's pick." | no |
| `docs/rulings` | `the-readme-is-in-asd-ste100-simplified-technical-english` | P | the list: "The README is in ASD-STE100 Simplified Technical English." (and two bullets of its own: "The skill files keep their own voice." and "An example in the README that no run produced says that it is an illustration") | no |
| `docs/rulings` | `the-readme-is-easy-for-a-reader-who-is-not-a-native-speaker` | M | the list, in the bullet "The README is in ASD-STE100 Simplified Technical English." (easy for a reader who is not a native speaker; no word that only Lem uses as a noun ("ask")) | no |
| `docs/rulings` | `the-readme-and-the-docs-do-not-report-what-ran` | P | the list: "The README and the docs do not report what ran." | no |
| `docs/rulings` | `the-readme-shows-the-interaction-and-links-to-no-run` | M | the list, in the bullet "The README and the docs do not report what ran." (the README shows the interaction in short form or a small flowchart, and links to no run) | no |
| `docs/rulings` | `no-history-and-no-reasons-in-a-text-for-a-reader` | P | the list: "No history and no reasons in a text for a reader." | no |
| `docs/rulings` | `lems-docs-do-not-speak-for-another-tool` | P | the list: "Lem's docs do not speak for another tool." | no |
| `docs/rulings` | `the-free-hour-may-edit-lems-skills-on-a-branch-of-the-clone` | P | the list: "The free hour may edit Lem's skills on a branch of the clone." | no |
| `docs/rulings` | `lem-naps` | P | the list: "Lem naps, and the naps are Lem's look back over its own memory." | no |
| `docs/rulings` | `the-naps-are-lems-look-back-over-its-own-memory` | M | the list, in the bullet "Lem naps, and the naps are Lem's look back over its own memory." (its adjustments, such as a nap that reads what Lem made of his corrections, are the session's form, in `skills/lem/prompts/nap.md`) | no |
| `docs/rulings` | `the-lessons-the-retro-and-jev-stay-a-night-run-ends-as-a-pull-request-naps-are-not-shown` | P | the list: "The lessons, the retro and Jev stay; a night run ends as a pull request; naps are not shown." | no |
| `.lem/decisions` | `a-night-ends-as-pull-requests-and-a-task-without-the-owner-covers-what-a-night-was` | M | the list, in the bullet "The lessons, the retro and Jev stay; a night run ends as a pull request; naps are not shown." (its brake is the history's line "A night's brake", kept in `skills/lem/stages/night.md`; its four at most is in "No setting counts the tasks that run") | no |
| `.lem/decisions` | `lem-is-a-companion-not-a-gate` | P | the list: "Lem is a companion, not a gate. (last part)" | no |
| `.lem/decisions` | `whether-a-change-is-careful-is-inferred-from-what-the-owner-said-must-not-go-wrong-never-matched-from-a-list-of-paths` | P | the list: "Whether a change is careful is inferred from what the owner said must not go wrong, never matched from a list of paths. (last part)" | no |
| `.lem/decisions` | `no-projects-session-edits-lem` | P | the list: "No project's session edits Lem. (last part)" | no |
| `.lem/decisions` | `the-mode-and-the-ladder-are-built-in-the-smaller-of-two-designs` | P | the list: "The mode and the ladder are built in the smaller of two designs. (last part)" | no |
| `.lem/decisions` | `an-ask-waits-for-another-task-only-when-it-needs-that-tasks-result` | E, now list | the list: "An ask waits for another task when it needs that task's result, not when it names the same code. (last part)" (E, back in the list: no check holds "not when it names the same code") | no |
| `.lem/decisions` | `a-task-that-ended-stays-ended` | E, now list | the list: "A task that ended stays ended. (last part)" (E, back in the list: no check holds `answered`) | no |
| `.lem/decisions` | `the-copied-talk-stays-in-lems-untracked-state-folder-and-never-reaches-git-or-a-pull-request` | E, now list | the list: "The copied talk stays in Lem's untracked state folder and never reaches git or a pull request. (last part)" (E, back in the list: no check holds "never reaches a pull request") | no |
| `.lem/decisions` | `lem-lands-lem-by-a-rule-not-by-machinery` | S | the list: "Lem lands Lem by a rule, not by machinery. (last part)" (S: what is left is its own bullet) | no |
| `.lem/decisions` | `two-reviews-of-the-release-and-what-the-session-took` | P | the list: "Two reviews of the release, and what the session took. (last part)" | no |
| `docs/rulings` | `the-question-page-is-a-part-of-lem-not-a-tool-the-machine-has-or-lacks` | E | the history, held by a test: "The question page is a part of Lem, not a tool the machine has or lacks." | no |
| `docs/rulings` | `a-task-has-a-type-and-a-track-and-they-are-two-words` | E | the history, held by a test: "A task has a type and a track, and they are two words." | no |
| `.lem/decisions` | `every-edit-of-the-settings-file-is-careful` | E | the history, held by a test: "Every edit of the settings file is careful." | no |
| `docs/rulings` | `a-personas-file-names-its-models` | E | the history, held by a test: "A persona's file names its models." | no |
| `.lem/decisions` | `lem-brings-its-own-builder-agent` | E | the history, held by a test: "Lem brings its own builder agent." | no |
| `.lem/decisions` | `a-plan-talks-record-is-taken-as-it-ran` | E | the history, held by a test: "A plan talk's record is taken as it ran." | no |
| `.lem/decisions` | `a-plan-never-makes-a-change-small` | E | the history, held by a test: "A plan never makes a change small." | no |
| `.lem/decisions` | `the-checks-remove-what-their-own-commands-leave` | E | the history, held by a test: "The checks remove what their own commands leave." | no |
| `docs/rulings` | `without-codex-one-expert-answers-alone` | E | the history, held by a test: "Without Codex one expert answers alone." | no |
| `docs/rulings` | `the-experts-know-the-personas` | E | the history, held by a test: "The experts know the personas." | no |
| `docs/rulings` | `a-project-can-close-branches` | E | the history, held by a test: "A project can close branches." | no |
| `docs/rulings` | `after-a-merge-lem-repairs-only-a-pull-request-with-a-conflict` | E | the history, held by a test: "After a merge, Lem repairs only a pull request with a conflict." | no |
| `docs/rulings` | `branch-history-is-squash-by-default` | E | the history, held by a test: "`branch.history` is `"squash"` by default." | no |
| `docs/rulings` | `a-polish-pass-is-a-step-of-the-flow` | E | the history, held by a test: "A polish pass is a step of the flow." | no |
| `docs/rulings` | `a-partial-review-is-a-review` | E | the history, held by a test: "A partial review is a review." | no |
| `.lem/decisions` | `a-lowered-bar-a-new-suppression-a-skipped-or-deleted-test-fewer-assertions-makes-a-pull-request-not-green-also-when-the-plan-gives-its-reason` | E | the history, held by a test: "A lowered bar (a new suppression, a skipped or deleted test, fewer assertions) makes a pull request not green also when the plan gives its reason." | no |
| `.lem/decisions` | `a-small-change-never-gets-a-polish-pass` | E | the history, held by a test: "A small change never gets a polish pass." | no |
| `docs/rulings` | `his-away-status-is-one-mark-of-the-machine-and-a-night-task-always-runs-without-him` | E | the history, held by a test: "His away status is one mark of the machine, and a night task always runs without him." | no |
| `docs/rulings` | `inside-a-phase-a-session-compacts-itself-at-his-number-for-all-his-repositories` | E | the history, held by a test: "Inside a phase a session compacts itself at his number, for all his repositories." | no |
| `docs/rulings` | `the-backlog-is-a-part-of-lem-and-its-view-is-a-tab-of-the-board` | E | the history, held by a test: "The backlog is a part of Lem, and its view is a tab of the board." | no |
| `docs/rulings` | `an-address-for-each-workspace-and-task-two-machines-under-one-and-pushes` | E | the history, held by a test: "An address for each workspace and task, two machines under one, and pushes." | no |
| `docs/rulings` | `he-acts-from-the-board` | E | the history, held by a test: "He acts from the board." | no |
| `docs/rulings` | `a-seat-is-written-agent-model-effort` | E | the history, held by a test: "A seat is written `agent/model:effort`." | no |
| `docs/rulings` | `the-state-of-lem-is-not-in-the-git-directory` | E | the history, held by a test: "The state of Lem is not in the git directory." | no |
| `docs/rulings` | `not-every-section-of-the-settings-stays` | E | the history, held by a test: "Not every section of the settings stays." | no |
| `docs/rulings` | `checks-keeps-three-keys-and-alone-is-serial` | E | the history, held by a test: "`[checks]` keeps three keys, and `alone` is `serial`." | no |
| `docs/rulings` | `four-places-are-settings` | E | the history, held by a test: "Four places are settings." | no |
| `.lem/decisions` | `one-machine-may-name-its-own-reviewer-for-a-while` | E | the history, held by a test: "One machine may name its own reviewer for a while." | no |
| `docs/rulings` | `as-a-plugin-the-correction-hook-comes-with-the-install-and-the-repository-says-yes-for-all` | E | the history, held by a test: "As a plugin, the correction hook comes with the install, and the repository says yes for all." | no |
| `docs/rulings` | `the-jev-model-comes-through-any-provider` | E | the history, held by a test: "The Jev model comes through any provider." | no |
| `.lem/decisions` | `one-person-can-say-no-to-the-correction-queue-and-nobody-is-switched-on-by-a-file-git-does-not-show` | E | the history, held by a test: "One person can say no to the correction queue, and nobody is switched on by a file git does not show." | no |
| `.lem/decisions` | `a-correction-hook-registered-twice-judges-each-message-once` | E | the history, held by a test: "A correction hook registered twice judges each message once." | no |
| `docs/rulings` | `each-of-the-three-seats-is-written-whole` | M | the history, in the line "A seat is written `agent/model:effort`." (its guard `tests/unit/test_settings.py::Seats.test_each_of_the_three_is_refused_unless_whole`; "a guide names the experts without a version" holds with no line, since no guide names them) | no |
| `.lem/decisions` | `the-reviewers-seat-is-written-agent-model-effort` | M | the history, in the line "A seat is written `agent/model:effort`." (the reviewer's seat is one of the three) | no |
| `docs/rulings` | `a-plans-file-is-yyyy-mm-dd-slug-md` | M | the history, in the line "Four places are settings." (its guard `tests/lem-settings.sh: "a plan's name is paths.plan_file, YYYY-MM-DD-<slug>.md by default"`) | no |
| `docs/rulings` | `the-correction-hook-is-an-optional-part` | M | the history, in the line "As a plugin, the correction hook comes with the install, and the repository says yes for all." (the hook is an optional part, which works only on the project's yes) | no |
| `.lem/decisions` | `where-the-stages-keep-what-the-amendment-of-2026-11-16-says-otherwise` | M | the history, in the line "A small change never gets a polish pass." (its criterion part is the history's line "A criterion a persona doubted stays as written until the owner sees it" (`skills/lem/stages/interview.md`); its "not green" for the experts' pick is in the bullet "The build asks him nothing") | no |
| `docs/rulings` | `a-release-is-a-change-of-the-plugins-version` | D | the history, kept in one place: "A release is a change of the plugin's `version`." (`docs/free-hour.md`) | no |
| `docs/rulings` | `a-shipped-skills-name-follows-lem` | D | the history, kept in one place: "A shipped skill's name follows `/lem`." (`AGENTS.md`, "Rules for a change here"; a line added there) | no |
| `.lem/decisions` | `the-sessions-answers-to-his-notes-that-asked-a-question-gate-is-renamed-checks-a-lead-queues-a-task-behind-another-open-task-whose-result-it-needs-and-the-plugins-commands-carry-lems-name` | D | the history, kept in one place: "The session's answers to his notes that asked a question." (`docs/settings.md`, `skills/lem/stages/plan.md`, `AGENTS.md`; a line added to `AGENTS.md` for the plugin's names) | no |
| `.lem/decisions` | `lem-build-takes-a-plan-file-too-and-lists-the-waiting-plans-when-it-gets-no-name` | D | the history, kept in one place: "`/lem build` takes a plan file too, and lists the waiting plans when it gets no name." (`skills/lem/stages/start.md`) | no |
| `.lem/decisions` | `the-size-of-a-change-decides-its-path` | D | the history, kept in one place: "The size of a change decides its path." (`skills/lem/SKILL.md`, `skills/lem/prompts/small.md`) | no |
| `docs/rulings` | `the-commands-of-his-status-and-of-a-task-are-lem-im-away-lem-im-back-lem-be-careful-task-lem-standard-track-task-and-lem-drop-task` | D | the history, kept in one place: "The commands of his status and of a task." (`skills/lem/SKILL.md`, "Subcommands") | no |
| `docs/rulings` | `the-investigation-of-a-bug-keeps-its-method` | D | the history, kept in one place: "The investigation of a bug keeps its method." (`skills/lem/prompts/investigator.md`) | no |
| `.lem/decisions` | `a-full-change-has-one-approval-and-no-ceremony-that-nobody-asked-for` | D | the history, kept in one place: "A full change has one approval and no ceremony that nobody asked for." (`skills/lem/stages/interview.md`) | no |
| `docs/rulings` | `the-plan-talk-is-predictably-short-over-a-closed-list` | D | the history, kept in one place: "The plan talk is predictably short, over a closed list." (`skills/lem/stages/talk.md`) | no |
| `docs/rulings` | `a-plan-may-end-with-a-documentation-task` | D | the history, kept in one place: "A plan may end with a documentation task." (`skills/lem/stages/plan.md`) | no |
| `docs/rulings` | `no-ci-on-a-push-for-now` | D | the history, kept in one place: "No CI on a push for now." (`.github/workflows/ci.yml`) | no |
| `docs/rulings` | `the-tests-are-chosen-by-what-can-fail-and-a-task-is-quick` | D | the history, kept in one place: "The tests are chosen by what can fail, and a task is quick." (`AGENTS.md`, "Checks"; a line added there: a journey is run once) | no |
| `.lem/decisions` | `two-builders-of-one-plan-that-run-at-one-moment-commit-only-their-own-paths` | D | the history, kept in one place: "Two builders of one plan that run at one moment commit only their own paths." (`agents/lem-builder.md`) | no |
| `docs/rulings` | `a-choice-that-matters-is-logged-also-when-nobody-was-asked` | D | the history, kept in one place: "A choice that matters is logged, also when nobody was asked." (`skills/lem/stages/ladder.md`) | no |
| `docs/rulings` | `lem-ask-expert-takes-a-question-in-words-or-none` | D | the history, kept in one place: "`/lem ask-expert` takes a question in words, or none." (`skills/lem-ask-expert/SKILL.md`) | no |
| `.lem/decisions` | `a-decision-of-the-plan-does-not-hold-the-task-held-keeps-what-has-no-options-the-criteria-that-wait-for-his-yes-one-more-fact-for-an-investigation-and-a-step-that-is-his-to-do` | S, now kept | the history, kept in one place: "A decision of the plan does not hold the task." (`skills/lem/SKILL.md`, the row `held`; S: what is left is kept there) | no |
| `.lem/decisions` | `a-machine-failure-stops-a-task-as-blocked-with-one-line-that-names-what-to-do-and-with-no-breakers-document` | D | the history, kept in one place: "A machine failure stops a task as `blocked`." (`skills/lem/SKILL.md`, the row `blocked`; a line added there) | no |
| `.lem/decisions` | `the-push-and-the-pull-request-of-propose-need-no-question` | D | the history, kept in one place: "The push and the pull request of `propose` need no question." (`skills/lem/stages/land.md`) | no |
| `.lem/decisions` | `the-boards-server-runs-the-merge-agents-merge-and-the-agent-only-writes-its-review` | D | the history, kept in one place: "The board's server runs the merge agent's merge, and the agent only writes its review." (`skills/lem/scripts/serve.py`) | no |
| `.lem/decisions` | `the-status-knows-what-merged` | S, now kept | the history, kept in one place: "The status knows what merged, and changes only what already happened." (`skills/lem/stages/status.md`; S: what is left is kept there) | no |
| `.lem/decisions` | `two-things-a-real-run-showed-on-2026-11-18` | S, now kept | the history, kept in one place: "Nobody else's word is his." (`skills/lem/stages/land.md`, step 8; S: what is left is kept there; the watch it names is now the board server's look at the forge) | no |
| `.lem/decisions` | `the-first-line-of-a-task-is-composed-by-lem-project-state-and-its-session-says-it-as-it-is` | D | the history, kept in one place: "The first line of a task is composed by `lem project state`, and its session says it as it is." (`skills/lem/scripts/project.py`, `skills/lem/prompts/session.md`) | no |
| `.lem/decisions` | `the-trials-of-2026-11-21-a-tasks-session-takes-the-focus-only-for-its-own-question-and-says-its-first-line-first-and-the-onboarding-writes-no-allow-rules-and-commits-the-plugins-file` | D | the history, kept in one place: "The trials of 2026-11-21." (`skills/lem/prompts/session.md`, `skills/lem/stages/init.md`) | no |
| `docs/rulings` | `a-board-of-example-tasks-says-so-on-the-page` | D | the history, kept in one place: "A board of example tasks says so on the page, and a line that waits for him says where he answers." (`skills/lem/scripts/lem_board_pages.py`) | no |
| `docs/rulings` | `the-time-card-gets-exact-start-times` | D | the history, kept in one place: "The time card gets exact start times." (`skills/lem/SKILL.md`, `skills/lem/scripts/project.py`) | no |
| `docs/rulings` | `what-waits-for-the-owner-is-one-list-with-a-decision-for-each-item` | D | the history, kept in one place: "What waits for the owner is one list, with a decision for each item." (`skills/lem/SKILL.md`, `skills/lem/stages/status.md`) | no |
| `docs/rulings` | `a-chord-opens-a-list-of-the-tasks` | D | the history, kept in one place: "A chord opens a list of the tasks." (`skills/lem/scripts/picker.py`) | no |
| `docs/rulings` | `a-page-to-read-opens-as-a-companion` | D | the history, kept in one place: "A page to read opens as a companion." (`skills/lem/scripts/board.py`) | no |
| `docs/rulings` | `no-stale-pull-request-and-a-folded-header-on-a-phone` | D | the history, kept in one place: "No stale pull request, and a folded header on a phone." (`skills/lem/scripts/serve.py`, `skills/lem/scripts/lem_board_task.py`) | no |
| `docs/rulings` | `a-tasks-artifacts-have-one-map` | D | the history, kept in one place: "A task's artifacts have one map." (`skills/lem/scripts/lem_artifacts.py`) | no |
| `.lem/decisions` | `the-board-is-served-and-the-server-draws-it` | D | the history, kept in one place: "The board is served, and the server draws it." (`skills/lem/scripts/serve.py`, `skills/lem/SKILL.md`) | no |
| `docs/rulings` | `a-check-of-the-tracker-is-no-command-of-the-owners` | D | the history, kept in one place: "A check of the tracker is no command of the owner's." (`skills/lem-linear/SKILL.md`) | no |
| `docs/rulings` | `lem-read-key-shows-a-ticket` | D | the history, kept in one place: "`/lem read KEY` shows a ticket." (`skills/lem/SKILL.md`, "Subcommands") | no |
| `.lem/decisions` | `onboarding-asks-three-questions` | D | the history, kept in one place: "Onboarding asks three questions." (`skills/lem/stages/init.md`) | no |
| `docs/rulings` | `the-readme-tells-a-command-he-types-from-one-a-job-or-lem-runs` | D | the history, kept in one place: "The README tells a command he types from one a job or Lem runs." (`README.md`) | no |
| `docs/rulings` | `the-texts-assume-a-public-repository` | D | the history, kept in one place: "The texts assume a public repository." (`README.md`) | no |
| `docs/rulings` | `the-readme-says-a-plugin-that-works-closely-with-agterm-and-names-no-operating-system` | D | the history, kept in one place: "The README says a plugin that works closely with agterm, and names no operating system." (`README.md`) | no |
| `docs/rulings` | `each-label-of-a-chart-is-quoted` | D | the history, kept in one place: "Each label of a chart is quoted." (`AGENTS.md`, `skills/lem/prompts/writing.md`; a line added to `AGENTS.md` for `README.md` and `docs/`) | no |
| `.lem/decisions` | `the-texts-people-read-say-the-owner` | D | the history, kept in one place: "The texts people read say "the owner"." (`AGENTS.md`, "Rules for a change here"; a line added there) | no |
| `docs/rulings` | `the-tests-are-to-be-useful-and-fast` | M | the history, in the line "The tests are chosen by what can fail, and a task is quick." (the tests are to be useful and fast) | no |
| `.lem/decisions` | `lem-annotate-file-is-the-owners-verb-for-marking-up` | S | nowhere (replaced on 2026-11-18 by "Three more commands are no commands of his"; nothing of it is in force) | no |
| `.lem/decisions` | `two-rulings-that-say-one-rule-are-merged-when-one-of-them-next-changes-not-before` | D, now none | nowhere (the merge it put off is this change, on the owner's word of 2026-11-21; nothing of it is left to hold) | no |

# A project's rulings are one list file

careful: yes, because it reaches "Lem reads a project's settings wrong" (task 1 removes `paths.ruling_file`, gives `paths.rulings` a new meaning and edits `.lem/project.toml`) and "A change bends a ruling of the owner" (task 3 changes the words of "Four places are settings").

## Acceptance criteria

Size: full, because a settings key leaves, another changes its meaning, and the retro, the ladder and the question gate change how they write and read a ruling.

1. A project's rulings are one markdown file, which the settings name, `docs/rulings.md` unless they say otherwise. In a project whose settings name no rulings, `lem project path rulings` prints `ROOT/docs/rulings.md`, and `lem project show` gives no `ruling_file` and no `lem project ruling-file` command exists.
2. A settings file that still has the folder form is refused, with a message that names the fix:
   1. `.lem/project.toml` says `rulings = "docs/rulings"`.
   2. Every `lem` command that reads the settings stops with exit 1.
   3. The message names `paths.rulings`, says that it names the list file, and gives `rulings = "docs/rulings.md"` as the example.
   4. The same file with `rulings = "docs/rulings.md"` and a line `ruling_file = "<slug>.md"` is refused as a key Lem does not know, and the message lists `plans`, `plan_file` and `rulings`.
3. `lem project init` writes `rulings = "docs/rulings.md"` with a comment that says it is the list of your product decisions, one bullet for each, and writes no `ruling_file` line. `init` writes only the setting: the file comes with the first ruling.
4. The retro writes a ruling the owner approved as one bullet of the list, under the heading of its group: the owner approves "a refund never makes an invoice negative" on 2026-11-22, and the list gets `- **A refund never makes an invoice negative.** (2026-11-22)` under `## Invoices`; a project with no list yet gets the file, with its title and that heading. A group heading that the list does not have yet is added at the end of the list, and the retro puts a ruling under a heading of the list when one fits.
5. The question gate's judge and the ladder read the rulings as the bullets of the list, and a cite names the group's heading and the bullet's bold sentence: "docs/rulings.md, Invoices: A refund never makes an invoice negative."
6. Lem's own repository keeps the same form, and its documents say it:
   1. Its `.lem/project.toml` says `rulings = "docs/rulings/rulings.md"` and has no `ruling_file` line.
   2. `docs/rulings/rulings.md` holds the owner's ruling of 2026-11-22, a project's rulings are one list file, as one bullet.
   3. "Four places are settings" in `docs/rulings/history.md` names the plans folder, a plan's file name and the rulings file, and no ruling's file name.
   4. `docs/settings.md` and `docs/install.md` call the rulings one file, and no page of `docs/` says that a ruling is a file of its own. `docs/install.md` says where the file is, and that the retro writes a bullet only after the owner approves the ruling, in a pull request.

## Tasks

1. **The settings and the command** (criteria 1, 2, 3, and the settings part of 6). `paths.rulings` names the list file, a markdown file inside the repository, `docs/rulings.md` by default; `paths.ruling_file`, `RULING_FILE`, `FILE_PATTERNS["ruling_file"]` and the `ruling-file` subcommand go, and `cmd_plan_file` and `lem_plans` serve the plan only. A value that does not end with `.md` is refused with the message of criterion 2, and so is one that names a folder that exists, with a message that says `paths.rulings` names the list file and gives `rulings = "docs/rulings.md"` (talk, question 5). `lem corrections list`, the one command that reads `.lem/project.toml` and never loads it through `project.py`'s `load` (`corrections.py::collects`; `land.py` reads tables of it only after `project_now` loaded it, and `lem_state.py` reads `machine.toml`), loads the settings through `project.py` first and stops with exit 1 and its message, as criterion 2.2 asks of every command; `collects` itself stays as it is for the correction hook, which a settings error must not stop (the topic "The correction hook breaks the developer's session") (talk, question 4); `skills/lem/scripts/corrections.py` and its unit test are files of this task. The `init` template writes the new line and its comment, "the list of your product decisions, one bullet for each", and makes no rulings file. `.lem/project.toml` of this repository says `rulings = "docs/rulings/rulings.md"`, with its comment, and no `ruling_file`. `docs/settings.md` gets one row for `paths.rulings` ("the file of your rulings, one bullet for each") and loses the `ruling_file` row; `tests/lem-settings.sh` checks the table against `project.py`, so both change in this task. The history line "Four places are settings" names its tests, which `tests/unit/test_agents_md.py` finds by name: the renamed check of `tests/lem-settings.sh` and the history line change together here. The settings become 20 keys: the count in the check of `tests/lem-settings.sh` ("the settings are 21 keys"), in its `pass` text and in the history line "Not every section of the settings stays", which cites that text, change together (talk, question 9). An unknown key's message lists the valid keys of its table always, after the near one when `difflib` finds one (`nearest`): for `ruling_file` it says `did you mean 'plan_file'?` and then `valid: plans, plan_file, rulings`, as criterion 2.4 asks (talk, question 6). The `paths.rulings` row of `docs/settings.md` shows a bullet's form, `- **The rule in one sentence.** (YYYY-MM-DD)` under the `##` heading of its group (talk, question 9). Which Lem runs while this task is open (talk, question 1): until the merge, `main:.lem/project.toml` still holds `ruling_file`, and the new `project.py` reads the base's copy in a task's worktree (`load`, `base_raw`), so the new code run in this worktree refuses that copy. No step of the task runs it there: the `lem` on the task's `PATH` is the installed Lem (`AGENTS.md`, "Checks"), which reads the branch's new `rulings` line as a path it only resolves and the base's two old lines as keys it knows, and every check of the new code runs in a throwaway repository, as `tests/lem-settings.sh` and `tests/unit/test_settings.py` do. A builder tries the new code the same way, never by `python3 skills/lem/scripts/project.py` in this worktree. After the merge, a worktree whose branch was cut before it carries the old lines, and the next Lem refuses them with the message of criterion 2; the maintaining session corrects such a branch by hand, as "Lem is not released" in `AGENTS.md` says. Files: `skills/lem/scripts/project.py`, `skills/lem/scripts/lem_plans.py`, `.lem/project.toml`, `docs/settings.md`, `docs/rulings/history.md`, `tests/lem-settings.sh`, `tests/unit/test_settings.py`, and the unit test of `lem_plans` when one names `RULING_FILE`.
2. **The readers and the writer** (criteria 4 and 5). `stages/learn.md`: a ruling is one bullet of the list `lem project path rulings` prints, under the heading of its group, in the form of criterion 4, a list that does not exist is made with a `#` title and the group's `##` heading, a group heading the list does not have is added at its end, and a ruling goes under a heading of the list when one fits; a ruling that replaces one of the list takes its bullet's place, and one that changes a part of another changes that bullet's words, so that the list never holds two rulings that disagree (talk, question 7); the retro's proposal of a ruling says the list, not "his rulings folder". A bullet of the list is written only on the owner's approval of that ruling (talk, question 2): in "learn, in the session" step 3 already asks for it ("make it on the owner's apply"), and in "The correction queue" a lesson whose file is the list is put to him as a move, as a lesson that came back is, also the first time, so "Nobody is asked" does not hold for a ruling; he approves it where he approves every move of a retro, its one question or its file of proposals. `stages/ladder.md`, level 0: a bullet of the list. `stages/init.md`: "no ruling file is written" and "three ruling files" say rulings. `skills/lem-gate/references/judge.md`: the judge greps the list file, a `##` heading is the area and a bullet is a ruling, and the cite of `decided` is the heading and the bold sentence; the judge reads the whole bullet, the lines after its bold sentence too, since they hold the ruling's limit, and answers `decided` only when the whole bullet answers the question as asked (talk, question 3); `skills/lem-gate/SKILL.md` says the same of `decided`. `skills/lem-panel/SKILL.md` line 20 names a real project's folder: it says the list `lem project path rulings` prints. `.lem/lessons.md`: the `learn:` line keeps only what is this repository's own (talk, question 7): the groups of its list are the twelve `tests/unit/test_agents_md.py` names in `GROUPS`, so the retro adds no group there, and "Choices of the maintaining session" stays the list's last part; the `lem-gate:` line keeps only what is this repository's own, `docs/rulings/history.md` beside the list and the part "Choices of the maintaining session". Files: those named.
3. **The documents, the ruling and the backlog** (the rest of criterion 6). `docs/rulings/rulings.md` gets the owner's ruling of 2026-11-22 as one bullet under "The settings, the seats and the tracker", in the form `AGENTS.md` gives. `docs/rulings/history.md`: "Four places are settings" becomes the three places, the plans folder, a plan's file name and the rulings file, with its day of 2026-11-22 added, if task 1 did not already change its words. `docs/install.md` line 56 names the rulings file in place of `docs/rulings/`, says where it is (`docs/rulings.md` unless the settings say otherwise), and says that the retro writes a bullet only after the owner approves the ruling, in a pull request. The module docstring and the help of `project.py` say "the rulings file" where task 1 left "folder". `docs/backlog/a-project-s-rulings-are-still-one-file-for-each-ruling.md` is removed with `git rm`. Files: those named, and any page of `docs/`, `README.md` or `site/` that a `grep -rn -i "ruling"` shows to call a ruling a file of its own.

## Plan talk

Who argued the plan: the reviewer, Codex, with GPT 6.2 Sol at high effort as its pane's status line
showed them (context 3% used at its start); the defender, Claude Code, with Opus 5.5 at high effort,
as the `defender:` line of the task's state gives. Two families. Seven turns, under the bound of 38
for its 9 questions. Agreement carries no authority: the review before the pull request reads each
settled position as a claim.

The list, numbered as the reviewer gave it in its first turn:

1. **Which Lem runs while the task is open.** In a task's worktree the new `project.py` parses the
   base's copy of `.lem/project.toml` with the new keys (`load`, `base_raw`), and `main` still holds
   `ruling_file`; `land.py::project_now` loads the base too. Repaired: task 1 says that the `lem` on
   the task's `PATH` is the installed Lem (`AGENTS.md`, "Checks"), which reads the branch's new line
   and the base's old ones, that every check of the new code runs in a throwaway repository, and that
   a branch cut before the merge is corrected by hand ("Lem is not released"). The reviewer checked
   the installed `settings_of` and `decide` on both texts. Closed: settled by the two, not checked by
   the review.
2. **What stops a first-time correction from becoming an unapproved ruling.** "The correction queue"
   of `stages/learn.md` writes a first-time lesson with "Nobody is asked" into the file of step 2,
   which the list becomes. Repaired: a bullet of the list is written only on the owner's approval; in
   the queue a lesson whose file is the list goes to him as a move also the first time. Closed, at the
   cause, on criteria 4 and 6.4: settled by the two, not checked by the review.
3. **What makes a bullet of the list an owner's ruling at the gate.** Lem's list holds the session's
   choices in its last part, a bullet's limit is in its lines after the bold sentence, and
   `docs/rulings/history.md` holds rulings still in force that the old folder scan reached and the
   list scan does not (`skills/lem-gate/references/judge.md`, source 1). Repaired once: the judge reads
   the whole bullet and answers `decided` only when the whole bullet answers the question; the
   reviewer called that at the cause for the limits. Held: the judge's brief does not reach this
   repository's `lem-gate:` lesson line. Refuted once: each line of the history is held by a test or
   the code, which the judge's `checkable` reaches; `AGENTS.md`, its fifth source, names the history
   and the list's last part; the last part opens with "None of these is his ruling". Held a second
   time: the required read is the bullet and its heading, not the part's opening line, and the order of
   the judge's sources does not lead to the history. **A design choice**: the kept decision (the judge
   reads the list's bullets, and this repository's history and choices stay in its own `lem-gate:`
   lesson line) against the changed one (the gate's brief carries the project's `lem-gate:` lines to
   the judge, and the judge reads the opening line of the part a bullet stands in). The ladder took it after the
   talk, and the question gate settled it as `cheap` for the kept decision, as task 2 writes it:
   either pick is a few lines of two texts, reversed in one commit, and only Lem's own list has a
   choices part and a history (decision 5 of the task's record).
4. **Which commands refuse the folder form.** `lem corrections list` reads `.lem/project.toml` through
   `corrections.py::collects`, which reads one key and never refuses. Refuted once: `collects` is the
   hook's, which a settings error must not stop. Held: criterion 2.2 says every command that reads the
   settings. Repaired: `lem corrections list` loads the settings through `project.py` first and stops;
   `collects` stays for the hook. Closed, at the cause, on criterion 2.2: settled by the two, not
   checked by the review.
5. **How the setting refuses a folder with a markdown name.** A folder at `docs/rulings.md` passes the
   `.md` check, and `decide` reports it as there. Refuted once as an addition with no realistic input.
   Held: criterion 1 asks for a file. Repaired: a `paths.rulings` that names a folder that exists is
   refused with the message of criterion 2; this widens the plan's decision on the `.md` check. Closed,
   at the cause: settled by the two, not checked by the review.
6. **How the unknown-key message meets criterion 2.4.** `nearest` gives `did you mean 'plan_file'?`
   for `ruling_file` (`difflib.get_close_matches`, checked by both) and then no list. Repaired: the
   message lists the valid keys of its table always, after the near one. Closed, at the cause, on
   criterion 2.4: settled by the two, not checked by the review.
7. **How the retro applies the list's rules in Lem's own repository.** A group added at the end
   breaks `tests/unit/test_agents_md.py::TheList.test_each_heading_is_a_group_in_its_order_and_the_last_part_closes_the_list`,
   and an appended replacement leaves two rulings in force. Repaired: `stages/learn.md` says a ruling
   that replaces one takes its bullet's place and one that changes a part changes its words, and the
   `learn:` line of `.lem/lessons.md` stays with this repository's twelve groups and its last part.
   Closed, at the cause: settled by the two, not checked by the review.
8. **What run shows the texts meet criteria 4 and 5.** "Not verified" names a real retro and a real
   gate run. Refuted twice: a stage text's test is a real task (`AGENTS.md`, "Checks"), and a retro's
   write needs the owner's approval, which the build never asks (`skills/lem/SKILL.md`, "What holds in
   every stage"). Closed: settled by the two, not checked by the review.
9. **Which counts and texts change with the tests.** The settings become 20 keys, cited in
   `tests/lem-settings.sh` and in the history line "Not every section of the settings stays", and the
   task's "Done when" asks `docs/settings.md` to show a bullet's form. Repaired in task 1. Closed:
   settled by the two, not checked by the review.

Each mechanism a repair added, with the decision it sits on and the reviewer's word:

- the owner's approval before a bullet is written, also for a first-time lesson (question 2): at the
  cause, on criteria 4 and 6.4;
- the judge's read of the whole bullet (question 3): at the cause for a ruling's limits;
- the load of the settings in `lem corrections list` (question 4): at the cause, on criterion 2.2;
- the refusal of a folder at `paths.rulings` (question 5): at the cause, the plan's decision on the
  `.md` check made whole.

No question was raised after the first turn. No addition was refused as unpriced.

What changed in the plan, by question and by task (commits `caa892a` and `2e2427a`):

- Task 1: which Lem runs, and how a builder tries the new code (question 1); the refusal of a folder
  (question 5); `lem corrections list` and its files (question 4); the unknown-key message (question
  6); the count of 20 keys, its history line, and the bullet's form on the settings page (question 9).
- Task 2: the owner's approval before a bullet, and the queue's first-time path (question 2); the
  judge's read of the whole bullet (question 3); a replacement takes its bullet's place, and the
  `learn:` lesson line stays (question 7).

## Decisions

- **The default is `docs/rulings.md`, a file and no folder.** The owner chose option 2 of the backlog item, whose words are "`paths.rulings` names a file in place of a folder". A folder for one file adds a level for nothing. Lem's own repository keeps `docs/rulings/rulings.md`, since `docs/rulings/history.md` stands beside it.
- **`lem project ruling-file` is removed, and `ruling_file` is refused as any unknown key is.** The ruling "No word and no form of a Lem before is kept" forbids a special refusal of a key that went.
- **A value of `paths.rulings` that is no `.md` file is refused.** It is the check of the new form (a plan's file name is checked the same way), and it stops the old folder form from being read as a file that does not exist.
- **Only the list.** A project gets no `history.md`: that file is Lem's own maintaining practice, written in this repository's `AGENTS.md`.

## Not verified

- The retro's and the gate's new texts run in no test: they are stage texts, and a real retro and a real gate run are their test (`AGENTS.md`, "A change to a stage file has no test").
- mybaze is not touched: its 71 files, its `_is_ruling` test and its 10 citing files move by hand after the merge (the ask).

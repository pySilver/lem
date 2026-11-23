# The plan talk's Claude Code reviewer can read and cannot write

careful: yes, because the owner says so, and the change sets what the plan talk's reviewer may write, which reaches the owner's topic "A builder or a lead works outside its brief: it edits the main checkout, another task's worktree or a branch it does not own": the reviewer's pane stands in the main checkout, and a wrong launch line leaves it free to edit there or stops the talk.

## Acceptance criteria

Size: full, because the change is careful and rests on one real talk in agterm before any file changes.

1. A plan talk's Claude Code reviewer reads the repository and cannot change a file of it:
   1. A talk opens in a throwaway repository on this Mac, with the owner's own Claude Code settings and the reviewer `claude/opus:high`.
   2. The reviewer reads `plan.md` and runs `git log` there, with no question in the reviewer's pane.
   3. The reviewer tries to write a line into `plan.md` with its file tool, and once more with a shell command.
   4. Claude Code refuses both writes with no question in the reviewer's pane, and `git status` in the repository shows no change.
   5. The reviewer tries a write into a second worktree of the throwaway repository, as another task's worktree in the main checkout, and Claude Code refuses it.
   6. The probe runs once more with every shell command and every edit allowed and the questions skipped, as a teammate's settings may have them, and gets the same refusals.
   - no test: one real talk in agterm shows it; its screens and `git status` go into the builder's report, since no suite starts agterm and Claude Code
2. The reviewer still answers through the mailbox:
   1. In the same talk, the reviewer writes a long answer into a file under `/tmp`, outside the repository.
   2. It sends its message, which names that file, with `mailbox-chat.py say`, and the send prints no error.
   3. The message reaches the defender's pane, and the defender reads the file.
   4. A write into the home folder, outside `/tmp`, is refused.
   - no test: the same real talk shows it, with the three receipts in the builder's report
3. `skills/lem/harness/claude-code/second-opinion.md` gives the launch line that the talk showed, and only that one: its Claude Code line starts Claude Code with the seat's model and effort, the reviewer's brief, and a guard that refuses every write into a repository and lets the mailbox send and the write under `/tmp` through. The guard is only on the launch line, or in a file of Lem's that the line names: Lem writes no file in the developer's Claude Code settings and none in the repository. When the talk did not show criteria 1 and 2, the harness file stays as it is, the backlog item in Lem's own `docs/backlog/` says what the talk showed, and the pull request says that the reviewer can still write.
   - no test: a sentence of the harness file

## How it works

```mermaid
flowchart TD
  A["The real talk runs with the new launch line"] --> B{"Every write of criteria 1 and 2 refused (the plan by its file tool and by a shell, the second worktree, the home folder, the agterm socket), no question, the bypass run in its own mode, reads work, three mailbox receipts?"}
  B -->|"yes"| C["second-opinion.md gives the new line, and the backlog item leaves"]
  B -->|"no"| D["second-opinion.md stays, and the backlog item says what the talk showed"]
```

## Tasks

1. **The probe, then the real talk.** First find the guard with `claude -p` runs in a throwaway
   git repository under the task directory, each with the owner's own settings loaded and one
   candidate guard (decisions 1 to 5): an `Edit` of `plan.md`, a `Write` of a new file there, a
   shell write there (`echo x >> plan.md`), a shell write into a second worktree of that
   repository (`git worktree add`, made before the run), a shell write of a file in the home
   folder, a shell write of `/tmp/lem-reviewer-probe.txt`, `git log`, a plain `agtermctl session
   new --command "touch FILE"` with FILE in the home folder (decision 4), and a send with another
   program in front (`AGTERMCTL=/usr/bin/touch mailbox-chat.py say --file F`). Keep the narrowest
   guard that refuses the five writes outside `/tmp` and both socket probes, and lets the `/tmp`
   write and `git log` through with no question. Run the kept guard once more as a teammate whose
   settings allow everything (criterion 1, step 6): the owner's `~/.claude/settings.json` sets
   `disableBypassPermissionsMode = "disable"`, which keeps `bypassPermissions` from taking, so this
   run drops his user settings with `--setting-sources project,local`, puts the teammate's allow
   rules for every shell command and every file tool in the throwaway repository's
   `.claude/settings.local.json`, and starts with `--permission-mode bypassPermissions` and
   `--output-format stream-json`. Record the `permissionMode` its `system` `init` line reports,
   and that the same writes are refused; a mode other than `bypassPermissions` there means step 6
   is not shown. Then open a pair in agterm whose session and panes start in Lem's main
   checkout, as a real talk's pair does (`plan-talk.md`, step 1, `MAIN`): a Claude Code agent as
   the defender in one pane, and the Claude Code reviewer in the other, started by the
   `second-opinion` steps with the candidate line and `skills/lem/prompts/reviewer.md` as its
   brief. The defender's message names the throwaway repository as the directory to work in, as a
   real talk names the worktree, and sends a short `plan.md` there with one wrong path. It asks the
   reviewer to read it, run `git log`, fix the path itself with its file tool, then with a shell
   command, write one line into the repository's second worktree and one into a file in the home
   folder, start a session through `agtermctl session new`, and to answer with its long text in a
   file under `/tmp` and a short message, itself a file under `/tmp` that names the long one, sent
   with `mailbox-chat.py say --file` (decision 4). Record each refusal and its words, that no permission question showed in the
   reviewer's pane, the reviewer's screen, `git status` of the throwaway repository and of the main
   checkout, the `/tmp` file, the send's JSON and the defender's receipt, and the model and effort
   the reviewer's status line shows. Close every session and pane the task opened, and remove the
   throwaway repository's files only from the task directory. Serves criteria 1 and 2. Touches no
   file of the repository; its record goes into the task directory, `reports/task-1.md`.
2. **The harness file, by what task 1 showed.** When task 1 showed criteria 1 and 2:
   `skills/lem/harness/claude-code/second-opinion.md`, step 2, gives the Claude Code line that ran,
   with one sentence on what the guard refuses and what it lets through, its source and day (the
   talk of this task), and one on what it does not hold, from task 1's record (a command the
   developer's own settings run outside the sandbox, a write grant of his outside the folder the
   guard denies, and `/tmp` with the per-user temp folder). When the guard is a file,
   it goes in `skills/lem/harness/claude-code/` beside the harness part, and the line names it by
   absolute path, as it names `prompts/reviewer.md`. The last note, "Not run yet", loses the Claude
   Code reviewer; `git rm` of
   `docs/backlog/the-plan-talks-claude-code-reviewer-has-no-read-only-guard.md`. Otherwise:
   `second-opinion.md` stays, and the backlog item is rewritten with what the talk showed. Serves
   criterion 3.

## Decisions

1. **The guard goes on the launch line, as a `--settings` value**, the same place the Codex guard
   took. It changes no file of the developer's. It rests on the ruling "Another program's settings
   stay where that program keeps them" and on the Codex line of
   `docs/plans/2026-11-21-plan-reviewer-read-only.md`, decision 1. `claude --help` (2.1.330, read
   2026-11-23) gives `--settings <file-or-json>`, "Settings file or JSON string to load more
   settings from". Whether the value is a JSON string on the line or a file Lem ships is task 1's
   finding: a file keeps the typed line free of nested quotes in fish and zsh.
2. **The file tools are denied by permission rules** (`Edit`, `Write`, `NotebookEdit` under
   `permissions.deny`). A deny rule wins over an allow rule in every settings scope, so the
   owner's `defaultMode = "auto"` in `~/.claude/settings.json` (its line 33) and his allow rules
   do not let an edit through. The reviewer writes its `/tmp` file with a shell command, under
   decision 3.
3. **A shell command runs in Claude Code's sandbox, and writes only under `/tmp`.** `sandbox.enabled`,
   `sandbox.failIfUnavailable` and `sandbox.allowUnsandboxedCommands = false`: the docs' strict
   sandbox mode, in which Claude Code ignores the `dangerouslyDisableSandbox` retry
   (code.claude.com, settings reference, read 2026-11-23 through Context7). The sandbox writes the
   working directory, the per-user temp folder and every `allowWrite`, `additionalDirectories` or
   `Edit` allow path of each settings scope the session loads (the same reference,
   `sandbox.filesystem.allowWrite`), and `denyWrite` wins inside a writable folder (its
   `denyWrite`). So the guard denies the whole home folder (`denyWrite` of `~`), which holds the
   main checkout, the task worktrees under it (`project.py`, `cmd_worktree`) and every path a
   developer's own grant opens under home, and allows `/tmp` (`allowWrite`). The writable set is
   then `/tmp`, the per-user temp folder, and a grant of the developer's outside home; the owner's
   `~/.claude/settings.json` has none (no `allowWrite`, no `additionalDirectories`, no `Edit`
   allow rule, read 2026-11-23), and task 2's sentence names that case as outside the guard. A
   repository under `/tmp` stays writable: criterion 3 lets the write under `/tmp` through, and no
   task's worktree or state is there. `/tmp` is the whole folder, not one file: the reviewer's
   message files take any name (decision 4). Whether `~` in `denyWrite` leaves the reads of
   criterion 1, step 2, working is task 1's finding; when it does not, the working directory is the
   second candidate, and the harness then names the developer's grants under home as outside the
   guard. The exact path forms (`/tmp` or `/private/tmp`, `~`) are task 1's finding too.
4. **The send runs outside the sandbox, and no sandboxed command reaches agterm's socket.**
   `mailbox-chat.py say` talks to agterm over its Unix socket (`ctl_args` in
   `~/.local/bin/mailbox-chat.py` passes `$AGTERM_SOCKET`), and that socket also starts a session
   with any command (`agtermctl session new --command`, `plan-talk.md`, step 1) and types into any
   pane (`agtermctl session type`), outside the sandbox. So the guard names no socket in
   `sandbox.network.allowUnixSockets`, and the macOS sandbox blocks every Unix socket then (the same
   reference). The one send goes through `sandbox.excludedCommands` with the entry
   `mailbox-chat.py say --file *`, and `permissions.allow` gets `Bash(mailbox-chat.py say --file *)`
   so that the owner's auto mode asks no classifier and no question (an excluded command "goes
   through the regular permission flow", the sandboxing page). It is `--file`, not `--stdin`: a
   call with a `<<EOF` heredoc stays in the sandbox under any entry (the settings reference,
   `excludedCommands`). This is the Codex guard's shape: there, too, the mailbox's send is the one
   command that runs outside the sandbox (`second-opinion.md`, step 2). A send with another
   program set in front (`AGTERMCTL=... mailbox-chat.py say --file F`) and a plain
   `agtermctl session new` are probes of task 1, and both must stay refused.
5. **The developer's own settings still load.** No `--setting-sources`, no `--safe-mode`, no
   `--restricted`: the reviewer receives its mail through his mailbox hook, and his login and model
   settings stay his. What his settings add that runs outside the sandbox (an `excludedCommands`
   entry of his) is outside the guard, and task 2's sentence says so when task 1 finds one.
6. **The line keeps `--model "MODEL" --effort "EFFORT"` and `--append-system-prompt`.** The seat
   names model and effort, and `second-opinion.md` reads them back from the status line. The first
   prompt gains one sentence of decision 4: each answer is a file under `/tmp`, sent with
   `mailbox-chat.py say --file PATH`; the Claude side of the mailbox sends with a heredoc by
   default (`~/.claude/skills/mailbox-chat/SKILL.md`, "Sending"), and that call stays sandboxed
   with no socket.

## What it will not verify

- The whole plan talk of Lem (`stages/talk.md`, its events and its record): task 1 runs the launch
  line, the reviewer's brief and the mailbox, which are what the change touches.
- Another Claude Code version than the installed 2.1.330, and Linux, whose sandbox has other
  socket rules (the same reference: `allowUnixSockets` is ignored there).
- A command the developer's own settings exclude from the sandbox: his word for every Claude Code
  session, which the ruling "Another program's settings stay where that program keeps them" keeps
  Lem out of.

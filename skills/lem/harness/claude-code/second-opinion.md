# Claude Code: second-opinion

A part of `../claude-code.md`, read when a session opens the reviewer's pane.

## second-opinion

The reviewer is a second agent in the split pane of the session that asks (the pair of a plan
talk, for a careful or large plan); the owner reads both panes. The settings hold the seat as one
line, `reviewer = "AGENT/MODEL:EFFORT"` under `[seats]`, and `lem project show` gives it parsed as
`seats.reviewer`: its `agent` (`claude` or `codex`), its `model` and its `effort`, and `seat`, the
line as written. The settings refuse a reviewer's seat with no model or no effort, so a seat that
is there names all three. The effort is the one of its pane for the plan talk, which is the one
thing this pane opens for.
When the settings name no reviewer (each part null), ask the owner once and write the answer into
`.lem/project.toml` as that line, whole.

The seat may be this machine's own for a while: the usual reviewer is down, or out of tokens.
`/lem reviewer AGENT/MODEL:EFFORT` (`/lem reviewer codex/gpt-6.2-sol:high`, or `/lem reviewer
claude/opus:high`) runs `lem project reviewer` with that seat, which
writes it into `.lem/project.local.toml` in the same form, a file git does not track; `/lem
reviewer default` removes it. Never change the seat by yourself. When the reviewer does not answer, or
says it is out of tokens, ask the owner once whether the other agent reviews for now, and write
the seat on his yes. While `lem project show` lists `seats.reviewer` under `local.overrides`,
every report says that the reviewer is this machine's choice, and "same family" when it is.

1. **Is a reviewer there?** `mailbox-chat.py status` names the other pane and what serves it:
   `claude`, `codex` or `none`.
2. **Open the seat** when there is no split or nothing serves it:
   - `agtermctl session split on --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET"`;
   - write the launch line to a file and type it into the right pane with
     `agtermctl session type --stdin --pane right --target "$AGTERM_SESSION_ID" --socket "$AGTERM_SOCKET" < FILE`.
     The line starts the agent with the reviewer's brief, `prompts/reviewer.md` in this skill's
     directory, by absolute path:
     - Codex: `codex -m "MODEL" -c "model_reasoning_effort=EFFORT" -a never -c 'default_permissions="lem_review"' -c "permissions.lem_review.filesystem={\":root\"=\"read\",\"/tmp/mailbox-chat-$AGTERM_PANE_ID.txt\"=\"write\"}" "$(cat "PATH/prompts/reviewer.md")"`.
       A Codex pane receives mail only after its first prompt, and the brief is that prompt.
       `$AGTERM_PANE_ID` stays as written: the reviewer pane's own shell expands it to its id.
       The profile `lem_review` reads the whole machine and writes one file, the reviewer's
       mailbox reply file `/tmp/mailbox-chat-<pane>.txt`, which the Codex mailbox recipe writes
       before `mailbox-chat.py say --file`; a bare `-s read-only` refuses that file and stops the
       talk (codex-cli 0.169.0, 2026-11-21), and `-a never` keeps a refused write from going to an
       approval reviewer of the developer's own Codex configuration. In two plan talks in agterm
       (codex-cli 0.169.0, 2026-11-22) Codex refused the reviewer's writes to the plan and to a
       file beside its reply file, took `/tmp` for `/private/tmp` by itself, and sent the reply.
       The profile does not hold a command that the developer's own Codex rules allow (an `allow`
       prefix rule in `~/.codex/rules/`): it runs outside the sandbox, by Codex's design and by
       his word for every Codex session, and the mailbox's own send is such a command.
       The profile lives on this line only: Lem writes no file of the developer's Codex settings.
     - Claude Code: `claude --model "MODEL" --effort "EFFORT" --settings "PATH/harness/claude-code/reviewer-guard.json" --append-system-prompt "$(cat "PATH/prompts/reviewer.md")" "You are the reviewer. Wait for the first message. Write each answer into a file under /tmp, then send it with mailbox-chat.py say --file PATH as a shell command of its own, with nothing before or after it."`
       The `PATH` after `--file` in the first prompt stays as written: the reviewer puts its own
       file there. The guard, `harness/claude-code/reviewer-guard.json` in this skill's
       directory, takes the file tools away (`Edit`, `Write`, `NotebookEdit` under
       `permissions.deny`) and runs every shell command in Claude Code's sandbox, with no retry
       outside it and no question to the developer's auto mode (`autoAllowBashIfSandboxed`). The
       sandbox refuses a write in the home folder (`denyWrite` of `~`), in the working directory
       (the deny rule `Edit(./**)`, since a `.` in `denyWrite` of a settings file means that
       file's own folder) and to every Unix socket, agterm's too; it writes `/private/tmp`
       (an `allowWrite` of `/tmp` opened nothing on macOS) and its own temp folder. The one send,
       `mailbox-chat.py say --file PATH`, runs outside the sandbox and reaches agterm; joined to
       another command in one shell call it stays inside and cannot, so the first prompt asks for
       it as a shell command of its own. In two plan talks in agterm and `claude -p` probe runs
       (Claude Code 2.1.330, 2026-11-23) Claude Code refused the reviewer's writes to the plan, to
       a second worktree and to the home folder, and the same under `bypassPermissions`, and the
       reply reached the defender; the talk that tried the writes had one more sentence in its
       first prompt, which asked for them. The guard does not hold what the developer's own
       Claude Code settings open: an `excludedCommands` entry runs outside the sandbox, an
       `allowUnixSockets` grant of agterm's socket lets a sandboxed command start a session with
       any command, and a write grant outside the home folder stays writable; nor a repository
       under `/tmp`. The guard lives on this line only: Lem writes no file of the developer's
       Claude Code settings.
     Keep the quotes around each value you put in: a skill's folder with a space splits a bare
     path, and zsh stops a bare model such as `opus[1m]` with "no matches found".
     `MODEL` and `EFFORT` are the seat's `model` and `effort` from `lem project show`.
   - read the model and the effort back from the pane's status line, and name those in the
     report, never the ones you asked for. When the status line shows no model or no effort (a
     status line of the owner's own may hide them), the report says `unread` for each, never the
     seat's value.
   - read `agtermctl tree --json` and confirm the session's `splitForeground` is that agent, then
     `mailbox-chat.py status` again.
   - Codex asks "Trust this folder?" the first time it starts in a repository, and it saves the
     answer in the owner's Codex configuration. That answer is the owner's: tell the owner that
     the reviewer's pane waits for it, and do not type into the pane. `mailbox-chat.py status`
     says `codex` once the pane listens.
   Under agterm's Live sessions mode, `agtermctl session restart --pane-id ID --command LINE` starts
   the same line without typing; in the other restore modes it is refused.
3. **Send the request** through the `mailbox-chat` skill: the plan's path, the directory to work
   in, the task it belongs to and the rule files
   that cover it (`lem project rules`, with the plan's files or `--range`). A message that names git goes from a file, never a heredoc.
4. **The reply arrives in this pane by itself.** Never poll for it, and check every claim it makes
   about the code with your own read before you act on it.
   A reply that may not be whole ("so far", a numbered point with no end) is answered in the same
   turn: accept or dispute its points and ask whether
   more follows. End the turn to wait only when the reviewer said that more follows.
5. **A reviewer is fresh for each review.** Before the next one, `agtermctl session split close`
   on this session ends the pane and its agent, and step 2 opens a new one. The dispute of a
   review's points and the check of the fixes it asked for belong to that review and stay in its
   pane. A plan talk is one review: every turn of it goes to the same pane.
   A new pane is not always a new Codex. With agterm's cookbook recipe for Codex session resume
   installed, a `codex` typed in a session continues that session's conversation: its wrapper
   keeps the session's Codex thread in `~/.codex/agterm/SESSION-ID` (the id in lower case), and
   every pane opened after it continues that thread (2026-11-14). So before the launch of step
   2, remove that file when it is there; after the launch, the pane's status line must show a
   context near zero. A reviewer that carries the last review reads the next one
   with it.

Say in the report which family reviewed. Two agents of one family agree more easily than two of
different ones; the report says "same family" when that was the case.

Not run yet: either line in a pane whose login shell is not fish. Both ran in fish only, and
their status lines showed the seat's model and effort (Codex 2026-11-22, Claude Code
2026-11-23).

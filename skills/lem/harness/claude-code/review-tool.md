# Claude Code: the review tool

A part of `../claude-code.md`, read at the first round of the review tool, or when a review routes one.

## The review tool

The review tool is `revmux:revmux`. It reads the project's lenses, prompts and profile from
`./.revmux` at the root of the checkout and from no other path, and `revmux init` writes its
starter set there (config, lenses, prompts). That folder is revmux's own, so it stays there in
every project, and the settings' `review` path names it; Lem never moves or links it, and
the learn stage writes a lesson into a lens, the profile or the rejected findings there.
What a profile or a lens is for: `revmux config`, run in the main checkout, prints each
profile with its `description` and its `roster` (the lenses each of its agents carries), and
each lens with its `description`. That output is what the review agent of `stages/land.md`
reads when it routes a review; the same lines head the files `prompts/profiles/NAME.md` and
`lenses/NAME.md`. In the starter set that `revmux init` writes, the profile for one small
read is `focused` ("for a small or time-boxed change": two agents), and the full set is the
profile the config names as its default, `comprehensive`. A project with other profiles says
in its `AGENTS.md` which one is its small read. A round runs one profile (`--profile NAME`),
or a set of lenses in the place of a profile's roster (`--lenses a,b`); no run with
`--lenses` was made here.
A review before a proposal runs in the main checkout, so that it reads the review folder as
the project has it and not as the change under review left it, with `--workdir` set to the
task's worktree and `--tasks-dir` set to the folder `reviews/` of the task directory. So the
round leaves nothing in the worktree, which the landing needs clean; revmux puts the round in
`reviews/SLUG/RUN/`, and the review agent puts the command's output and its log beside it.
The `revmux:revmux` skill is written for a session with a person: its questions to the user,
its status lines and its offers after a round are not for a review agent, which prepares the
round itself, asks nobody and stops after its two files.
A round's line, run from the main checkout: `revmux --task SLUG --run 01-initial --profile
focused --workdir WORKTREE --tasks-dir TASK_DIR/reviews --no-tui`; both checkouts were clean
after it (revmux v0.2.7, 2026-11-16). The flag `--config-dir PATH` does not name a project
folder: it puts PATH in the place of the user's own config folder (revmux v0.2.7, 2026-11-15).
A round runs in the background, as step 2 of the skill says, with its line wrapped in `agst`,
so that the task's session row in agterm shows `active` while the round runs. A background round
comes back to its review agent whatever its length: 92 of 92 did, the longest after 25.3 minutes
(a scan of the review agents' transcripts on one machine, 2026-11-24). A round in the foreground
does not: in a subagent, a command past the Bash tool's 10-minute limit is stopped with exit 143
and does not go on in the background (Claude Code 2.1.331, 2026-11-23).
`agst` is the wrapper of agterm's cookbook, `cookbook/long-commands-status/agst.sh` in
github.com/umputun/agterm, which a developer copies onto his `PATH`; agterm does not install it.
It marks the session in `AGTERM_SESSION_ID`, which the review agent's shell has from the task's
session, `active` before the command, then `completed --auto-reset` on exit 0 and `blocked
--auto-reset` on any other; outside agterm it only runs the command. revmux exits 1 when a round
reports findings (`references/output.md`, `revmux:revmux` 0.5.6), and `blocked` is the mark that
says a session waits for the owner (`mark-waiting` in `../claude-code.md`). So the line turns
that exit into 0, and only a failed round (revmux's 2 or 3, or 127 when it is not found) ends it
with 1 and marks the row `blocked`. The line, run with `run_in_background`, its stdout into the
output file and its stderr into the log:
`agst sh -c 'revmux "$@" || test $? -eq 1' revmux --task SLUG --run 01-initial --profile
focused --workdir WORKTREE --tasks-dir TASK_DIR/reviews --no-tui > OUTPUT 2> LOG`. Its exit
status says whether the round ran, never whether it found something: the findings are in the
output (revmux's exits 0, 1, 2 and 3 and a revmux not found, tried with stand-ins for revmux and
`agtermctl`, 2026-11-24).
Before the first round, `command -v agst` says whether it is on the `PATH`. When it is not, the
round runs the plain line given first, in the background as well, and `review-N.md`
says in one line that the row showed no mark of the round because `agst` is not on the `PATH`.
The round itself is the same.

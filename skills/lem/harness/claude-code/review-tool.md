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

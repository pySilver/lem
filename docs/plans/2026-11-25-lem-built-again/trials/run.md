# Order of the trial run

The orchestrator runs the commands. Ask the owner for the trial tag, tap revision, scratch forge
access, GUI session, phone, tailnet machines and project snapshot before their checks. Keep the
owner's live Lem installation, state, sessions and ports 4536 and 4537 out of the run.

| Order | Sheet | Folder to keep | Owner's part | Time, unmeasured estimate |
| --- | --- | --- | --- | --- |
| P1 | [Pack](pack.md) | Pack | Approve the tag and tap on the test Mac | 15 min |
| P2, P3, P4, P5, P6 | [Pack](pack.md) | Pack, same keg and plugin | GUI for P3 and P6 | 5, 10, 5, 5, 10 min |
| Mutation step | Part 9 of the plan | Separate | None | 45 min |
| R1, R2 | [Real](real.md) | One checkout per check | Answer the interview and breaker | 45, 20 min |
| R3, R4, R5 | [Real](real.md) | One per check, separate bases for R4 and R5 cases | R4 approval, R5 retry | 25, 35, 35 min |
| A1–A5 | [Ask](ask.md) | Ask, one server and task session | Answer on the Mac and phone | 35 min |
| R6, R7 | [Real](real.md) | Phone, then one folder on each peer | Phone and tailnet | 25, 25 min |
| R8, R9 | [Real](real.md) | Night, then Project | Approve the R9 snapshot and task | 30, 45 min |

Run P4 while the Mac is quiet. Complete P1–P6 before the mutation step. Use the same approved
release for the real trials. Complete the scratch tasks before R9. Stop at a failed dependency.
Keep its output and tell the orchestrator which later boxes wait for it.

## A folder per entry in the table

Use an absolute Python 3.14 binary as `PY` and the absolute `trials/bin` path as `BIN`. Set `T` to
a new absolute path below `/tmp` and `TRIAL_USER` to the trial account name. Pass `--tool` for each
executable the check uses, with its real absolute path. Add the keg's links after P1. For R5, omit
`gh` from the maker's tool list and add the R5 wrapper as described in its box.

```sh
umask 077
"$PY" -I -B "$BIN/make.py" "$T" --user "$TRIAL_USER" --tool "git=$GIT" --tool "claude=$CLAUDE"
ln -s "$KEG/lem" "$T/bin/lem"
ln -s "$KEG/lem-hook" "$T/bin/lem-hook"
```

Use the canonical `folder` from the maker's JSON as `T`. `T/enter` gives commands an empty
initial environment and assigns the trial home, config, cache, temp folder and PATH. `T/enter-gui`
uses `/usr/bin:/bin`. Use `T/step [options] NAME -- COMMAND ARG…` for evidence. `--cwd` is relative
to `T` or a path inside it. `--stdin` reads a file inside `T`. The step uses an empty stdin without
that option. The `.pid` file names the command process. A background board step holds until its
server stops. For a GUI pane, use `T/enter` directly and keep the pane evidence separately. Pass
only the scratch agterm connection variables a session requires. Check the homes and PATH in the
pane, its builders and companions before allowing writes. Use the private trial Claude Code
profile and the approved scratch credentials. Prepare `T/config/gh` with the trial login and run
`T/enter gh auth status`. Use `gh`'s HTTPS Git credential helper in the scratch home. Use approved
Claude Code login material only in the scratch profile. Keep secrets out of the command line and
of evidence. Do not copy the live Lem or Claude Code home.

For P2–P6 make a local pack checkout with `mkdir "$T/repo"`, then run
`T/step --cwd repo p1-local-git -- git init -b trial-pack` and
`T/step --cwd repo p1-local-lem -- lem init --base trial-pack`. For the real and ask trials,
use the fixture, server setup and cleanup in [the real sheet](real.md).

Keep screenshots, transcripts, forge snapshots and device results under `T/evidence`, with a
check name. Use `"$T/index" > "$T/index.json"` after the last capture. Keep `T`, its index and the
check results together. Note each check's evidence paths beside its box before the orchestrator
ticks it. A refusal expected by the check keeps its raw exit code. Give a rerun a new step name.

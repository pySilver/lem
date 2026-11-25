# The trial of the walking skeleton on real tools

The step `trial-skeleton` of part 9, run on 2026-11-25 from 06:14 to 06:25 (Central European
Time) on the owner's Mac. The app under trial is the keg that Homebrew built from the commit
`7bb16c2880935ad564c6907d0874ede2806ab702` of `rebuild`, not linked into `PATH`:
`/opt/homebrew/opt/lem/libexec/bin/lem` and `lem-hook`, the plugin files in
`/opt/homebrew/opt/lem/libexec/lib/python3.14/site-packages/lem/data`.

The trial folder is `/private/tmp/lem-trial.kN4dScjM` (T below). Every run of `lem` and
`lem-hook` went through `T/enter`, which starts the command with `env -i` and only these:
`HOME` and `USER` (for git's and gh's login), `GH_CONFIG_DIR=$HOME/.config/gh` (see finding 1),
`PATH=T/bin:/usr/bin:/bin` (`T/bin` holds links to the keg's `lem` and `lem-hook`, and to `gh`
and `git`), `XDG_CONFIG_HOME=T/config`, `TMPDIR=T/tmp` and `LEM_SERVE=off`. A check overrides one
of them where it says so. `T/step.py` ran each command of the landing and kept its stdout,
stderr, exit code and seconds as `T/evidence/NN-NAME.{out,err,meta}`. No agent session, no
agterm and no browser ran.

The scratch repository is `pySilver/lem-scratch`, cloned to `T/repo`. Its base for the trial is
the orphan branch `trial-sk-wren`: `docs/word-list.txt` (`recieve`), `tests/words.sh`, and
`.lem/settings.toml` (`[branch] base = "trial-sk-wren"`, `land = "agent"`, `history = "squash"`;
`[checks] commands = ["sh tests/words.sh"]`), with `.lem/.gitignore` as Lem's own repository has
it. The task's branch is `trial-sk-wren-receive`, named with `lem task worktree --branch`,
because the rule of the trial lets only `trial-sk-*` branches reach GitHub. A teammate's commit
(`85327cf`, `NOTES.md`, from a second clone `T/teammate`) went onto the base after the build, as
in `tests/journeys/test_skeleton.py`, so that `lem land base` rebased.

## The checks

- [ ] S1 `brew install --build-from-source --skip-link` from the scratch tap. Run by the session,
  not by this trial. The keg was built in 4 seconds, but the command ended with exit 1:

  ```text
  Error: Failed changing dylib ID of /opt/homebrew/Cellar/lem/0.3.1.2/libexec/lib/python3.14/site-packages/watchfiles/_rust_notify.abi3.so
  ... Updated load commands do not fit in the header of .../watchfiles/_rust_notify.abi3.so ... (MachO::HeaderPadError)
  Error: Failed to fix install linkage
  🍺  /opt/homebrew/Cellar/lem/0.3.1.2: 832 files, 9MB, built in 4 seconds
  ```

  Log: `/tmp/lem-trial-skeleton/s1-install.keep.out`. The extension still loads from the keg
  (`T/enter /opt/homebrew/opt/lem/libexec/bin/python -I -c "import watchfiles._rust_notify"`:
  exit 0; `otool -D` shows its id `@rpath/watchfiles._rust_notify.abi3.so`, not rewritten), and
  the board's stream ran on it in S6. Findings 2 and 3.

- [x] S2 `lem version` and `lem help` from the keg, with `PATH=/usr/bin:/bin`.

  ```text
  $ T/enter PATH=/usr/bin:/bin /opt/homebrew/opt/lem/libexec/bin/lem version     # exit 0, stderr empty
  {"root": "/opt/homebrew/Cellar/lem/0.3.1.2/libexec/lib/python3.14/site-packages/lem/data",
   "version": "0.3.1", "commit": "7bb16c2880935ad564c6907d0874ede2806ab702"}
  $ T/enter PATH=/usr/bin:/bin /opt/homebrew/opt/lem/libexec/bin/lem help        # exit 0, stderr empty
  Usage: lem [OPTIONS] COMMAND [ARGS]...  (task, criteria, decisions, land, session, ... issue)
  ```

  Evidence: `T/evidence/s2-version.{out,err}`, `T/evidence/s2-help.{out,err}`.

- [ ] S3 `forge_gh`'s contract suite against a scratch GitHub repository. Not run as worded: the
  contract suite (`tests/contract/test_forge_gh_slice.py`) runs on the stand-in for `gh` and was
  not pointed at GitHub. What ran instead is the real adapter on the plain path of S5: every
  call of `forge_gh` that path makes (`repo view`, `pr list --head --base --state all`,
  `pr create`, `pr view`, `pr merge --match-head-commit --squash --subject --body`, `api
  repos/OWNER/NAME/commits/SHA --jq .parents[0].sha`, and the `git push --force-with-lease
  origin :BRANCH` of `delete_ref`) answered as the adapter reads it. The adapter's read calls,
  run again by hand with its own words, gave the same shapes as the stand-in but for the points
  in finding 4:

  ```text
  $ T/enter gh pr view 20 --json number,url,title,body,state,headRefOid,headRefName,baseRefName,mergeable,mergeCommit,autoMergeRequest --repo pySilver/lem-scratch
  {"autoMergeRequest": null, "baseRefName": "trial-sk-wren", "headRefOid": "0de2bad...", "mergeCommit": null,
   "mergeable": "MERGEABLE", "number": 20, "state": "OPEN", ...}                       # exit 0
  $ T/enter gh pr list --head nothing-like-this --state all --json ... --repo pySilver/lem-scratch
  []                                                                                    # exit 0
  ```

  Evidence: `T/evidence/23-gh-adapter-view-open.json`, `22-`, `30-`, `40-gh-pr-*.json`.

- [x] S4 `session-start` through the manifest's line, `/bin/sh "$CLAUDE_PLUGIN_ROOT/hooks/run"
  session-start`, with `CLAUDE_PLUGIN_ROOT` the keg's data folder, `PATH=/usr/bin:/bin`,
  `CLAUDE_ENV_FILE=T/tmp/env-file*`, run in `T/repo`, and the event
  `{"hook_event_name": "SessionStart", "source": "startup", "session_id": "trial-0001",
  "transcript_path": "T/tmp/t.jsonl", "cwd": "T/repo"}` on stdin (`T/tmp/event-startup.json`).

  | Run | Exit | stdout | stderr | What it wrote |
  | --- | --- | --- | --- | --- |
  | a: `LEM_HOOK_BIN=/opt/homebrew/opt/lem/libexec/bin/lem-hook` | 0 | empty | empty | `T/tmp/env-file`: `export LEM_PLUGIN_ROOT='/opt/homebrew/opt/lem/libexec/lib/python3.14/site-packages/lem/data'` |
  | b: `LEM_HOOK_BIN` unset (the wrapper's Homebrew path) | 0 | empty | empty | the same line in `T/tmp/env-file-b` |
  | c: `LEM_TASK=word-list-says-receive`, after `task open` | 0 | empty | empty | the same line in `env-file-c`, and one framed line in `T/repo/.lem/state/tasks/word-list-says-receive/sessions.jsonl` |
  | d: the owner's old `lem` first on `PATH` | 0 | a `systemMessage` (finding 5) | empty | the same line in `env-file-d` |
  | e: `PATH=T/bin:/usr/bin:/bin`, the formula's `lem` first | 0 | empty | empty | the same line in `env-file-e` |
  | f: `not json` on stdin, with `LEM_TASK` | 0 | empty | empty | nothing |

  The framed line of run c, after its leading line end:

  ```text
  {"v": 1, "at": "2026-11-25T05:18:43Z", "source": "startup", "claude": "trial-0001",
   "transcript": "/private/tmp/lem-trial.kN4dScjM/tmp/t.jsonl", "task": "word-list-says-receive", "pane": null}
  ```

  Timing of 20 runs: see "Timings". The 20 timed runs with `LEM_TASK` added 20 more lines to the
  task's `sessions.jsonl` (21 framed lines in all). Evidence: `T/evidence/s4-*`.

- [ ] S5 a fast-track task from `/lem` to a merged pull request, in a session that loads the
  scratch plugin. Not ticked: no agent session ran (the stage texts still hold the old command
  lines). The trial ran the plain path's commands by hand, in the order and with the inputs of
  `tests/journeys/test_skeleton.py`, against real GitHub. Every step but the refusals asked for
  on purpose ended with exit 0, and before each step `lem land next` named that step:

  | `lem land next` said | Command (`T/evidence/`) | Exit | Result |
  | --- | --- | --- | --- |
  | (none) | `task open word-list-says-receive --ask "the word list says recieve; fix it"` (01) | 0 | `status: shaping` |
  | `none`, wait (02) | `task read ... --type docs --why ... --track small --then fast` (03) | 0 | the four fields |
  | | `criteria.md` written into the task's folder; `criteria approve ... --small` (04) | 0 | criterion 1, size small |
  | | `task worktree ... --branch trial-sk-wren-receive` (05) | 0 | `made: true` |
  | | `task move ... building --line "one builder"` (06) | 0 | `shaping` to `building` |
  | | in the worktree: `receive`, `git commit --all -m "docs: receive"` (`7505e29`); the `no test` line appended; `criteria record` in the worktree (07) | 0 | `no_test` recorded |
  | | the teammate's commit `85327cf` on the base; `task move ... ready --line built` in the worktree (08) | 0 | `building` to `ready` |
  | `start` (09) | `land start` (10) | 0 | round 1 |
  | `base` (11) | `land checks` early (12) | 1 | `not-due`, fix `lem land base ... is the step that is due` |
  | | `land base` (13) | 0 | tip `0de2bad`, base `85327cf`, before `7505e29` |
  | `checks` (14) | `land checks` (15) | 0 | `sh tests/words.sh` exit 0, `outcome: passed` |
  | `read` (16) | `land read` (17) | 0 | attempt 1, floor `read`, tip `0de2bad` |
  | | `land read --record T/tmp/review.json` (18): kind `read`, 0 must-fix, 0 should, 0 nit, no `outside` | 0 | the review on record |
  | `propose` (19) | `land file` (20) | 1 | `not-due`: with no `outside` finding `file` is not due, and `propose` is |
  | | `land propose --title "docs: the word list says receive" --notes T/tmp/notes.md` (21) | 0 | `green: true`, pull request 20 opened |
  | | `land propose` again (24) | 1 | `not-due` |
  | `merge-review` (25) | `land merge-review` (26) | 0 | the brief, tip and base |
  | | `land merge-review --file T/tmp/reply.md --tip 0de2bad... --base 85327cf...` (27), reply `merge` | 0 | `verdict: merge` |
  | `merge` (28) | `land merge --by merger --message "docs: the word list says receive"` (29) | 0 | merge commit `f37507c`, parent `85327cf` |
  | `merged` (31) | `land merge` again (32) | 1 | `not-due`: `lem land merged ... is the step that is due` |
  | | `land merged` (33) | 0 | the merge on record; the main checkout fast-forwarded to `f37507c` |
  | | `land merged` again (34) | 1 | `not-due`: it did nothing |
  | `clean` (35) | `land clean` (36) | 0 | `worktree_gone`, `branch_gone`, `forge_branch_gone`: all true |
  | `done` (37) | `land clean` again (38); `land merge` after the end (39) | 1, 1 | `not-due`: "no step is due: the landing ended" |

  After the propose:

  ```text
  $ T/enter gh pr view 20 --repo pySilver/lem-scratch --json state,headRefOid,baseRefName,mergeable
  {"baseRefName":"trial-sk-wren","headRefOid":"0de2baddd1b6b8b43e1dc14768fd1d2a3ee63ad7","mergeable":"MERGEABLE","state":"OPEN"}
  ```

  After the merge:

  ```text
  $ T/enter gh pr view 20 --repo pySilver/lem-scratch --json state,headRefOid,baseRefName,mergeable,mergeCommit,mergedAt,mergedBy
  {"baseRefName":"trial-sk-wren","headRefOid":"0de2bad...","mergeCommit":{"oid":"f37507c8963349757048702b08b71b2090eac092"},
   "mergeable":"UNKNOWN","mergedAt":"2026-11-25T05:21:34Z","mergedBy":{"login":"pySilver",...},"state":"MERGED"}
  $ T/enter gh api repos/pySilver/lem-scratch/commits/f37507c... --jq '{sha,parents:[.parents[].sha],message:.commit.message}'
  {"message":"docs: the word list says receive\n\nLem task: word-list-says-receive","parents":["85327cf..."],"sha":"f37507c..."}
  ```

  The cut of the brief: the first `land merge` merged, so it ran only once before the merge. After
  the merge, `land merge` refused `not-due` twice (32, 39) and the forge shows one merge: the
  base's history is `f37507c`, `85327cf`, `e4e9d6e`, one squash commit. `land merged` ran twice;
  the second refused `not-due` and changed nothing. At the end `task.json` says `status: landed`,
  `landing.phase: ended`; `git status --porcelain` in `T/repo` is empty; `git branch -a` has no
  `trial-sk-wren-receive`, and origin had no such branch before the trial deleted its base.

- [x] S6 the board. `T/serve_trial.py` picked port 59056 by a bind to port 0, started
  `T/enter /usr/bin/env -u LEM_SERVE lem --repo T/repo serve run --port 59056` as its own child
  (pid 90506), and read it with curl:

  ```text
  /api/server        200 {"pid":90506,"port":59056,"url":"http://127.0.0.1:59056/","host":"mac",
                          "install":{"version":"0.3.1","commit":"7bb16c2...","package":"/opt/homebrew/Cellar/lem/0.3.1.2/..."},
                          "home":"/private/tmp/lem-trial.kN4dScjM/config/lem","door":null,...}
  /                  501 {"step":"board-pages","why":"GET / is not built yet: ..."}
  /mac/repo/         200 <article class="tc s-landed" id="card-word-list-says-receive" ...>
                         <span class="tc-title">word-list-says-receive</span> ... <span>landed</span>
  ```

  `lem serve stop` first refused `owner-port` (finding 9). With `T/config/lem/machine.toml`
  holding `[serve] port = 59056`, `lem serve stop` gave `{"stopped":true,"pid":90506}`, the child
  ended with exit 0, nothing listened on 59056, and `serve run` printed
  `{"ok":true,"result":{"pid":90506,"port":59056,"url":"http://127.0.0.1:59056/"}}` with an empty
  stderr. A second run (`T/stream_trial.py`, pid 93647, same port) read
  `/mac/repo/stream` for 6 seconds while the task's `task.json` was touched: one event,
  `data: <turbo-stream action="refresh"></turbo-stream>`; then `lem serve stop` stopped it, exit
  0. After both, `lsof -iTCP:59056` found nothing and `ps` showed no process of the trial.
  Evidence: `T/evidence/s6-*`, `T/evidence/s6b-*`.

- [x] S7 the owner's machine, before the first command (06:16) and after the last (06:25 and
  again after the commit of this file):

  ```text
  $ ps -p 3311 -o pid=,lstart=
   3311 Tue Nov 24 00:31:16 2026
  $ ls /Users/Silver/Projects/GitHub/lem/.lem/state/tasks | wc -l
        98
  $ find ~/.config/lem -newermt "2026-11-25 06:20"
  (nothing)
  ```

  No command of the trial asked port 4536 or 4537: the only `lem serve stop` aimed at 4536 was
  refused `owner-port` before any connection (`board/machine.py: port_of` raises before
  `client.ask`). Lem wrote nothing under the real home. `gh` did: its HTTP cache
  `~/.cache/gh/c6/86/101fd671...` is of 06:21:30, the second of the merge (finding 10).

## Cleanup

`git push origin --delete trial-sk-wren` ran after the pull request's final state was on record
(`T/evidence/40-gh-pr-final.json`: number 20, `MERGED`, merge commit `f37507c`); Lem's
`land clean` had deleted `trial-sk-wren-receive` on origin. `git ls-remote --heads origin` shows
no `trial-sk-*` branch. Pull request 20 stays, merged, as the evidence; nothing else on GitHub
was opened or closed. T stays in place with `T/repo`, `T/teammate`, `T/config`, `T/evidence`.

## Findings

1. **`XDG_CONFIG_HOME` moves gh's login too.** `T/enter gh repo view pySilver/lem-scratch` with
   `XDG_CONFIG_HOME=T/config` exited 1 with `To get started with GitHub CLI, please run: gh auth
   login`: gh reads `$XDG_CONFIG_HOME/gh`. The trial set `GH_CONFIG_DIR=$HOME/.config/gh`. Lem
   itself has no defect here: a developer with `XDG_CONFIG_HOME` set keeps gh there as well. A
   test or trial that isolates Lem's home this way and runs the real `gh` must set
   `GH_CONFIG_DIR`. Owner: `pack-trial` and `trials` (their procedure).
2. **The install exits 1 on the watchfiles wheel.** `brew install --build-from-source
   --skip-link pySilver/tap/lem`: "Failed to fix install linkage", because Homebrew cannot write
   a new dylib id into `watchfiles/_rust_notify.abi3.so` ("Updated load commands do not fit in
   the header"). The keg works, but `brew` reports failure, and a `brew upgrade` will too. It
   should exit 0: the formula skips the relocation of that file (Homebrew's `skip_clean` or a
   build of watchfiles from source with `-headerpad_max_install_names`), or the stream does not
   need watchfiles. Owner: `pack-trial` (the formula); `board-pages` if the stream's library
   changes.
3. **The keg's version is `0.3.1.2`, the app says `0.3.1`.** `ls -la /opt/homebrew/opt/lem`
   points at `../Cellar/lem/0.3.1.2`; `lem version` and the plugin's manifest say `0.3.1`. The
   formula and the app should give one version. Owner: `pack-trial`.
4. **What the stand-in for `gh` answers and real GitHub does not.**
   - The squash's subject. With `gh pr merge 20 --squash --subject "docs: the word list says
     receive" --body ...`, GitHub wrote the subject as given:
     `docs: the word list says receive\n\nLem task: word-list-says-receive`. `LocalForge.merge`
     (`tests/fakes/forge.py:155`) writes `f"{text.subject} (#{number})"`, and
     `test_the_squash_takes_the_reports_subject_and_names_the_task` asserts that ` (#1)`. Either
     the adapter adds ` (#N)` to the subject it sends, or the fake and the test drop it. Owner:
     `land-propose` (the forge adapter and its contract), with `land-merge` for the text.
   - `mergeable` after the merge is `UNKNOWN` on GitHub (`T/evidence/30-gh-pr-view-after-merge.json`).
     The adapter does not read it there, so no defect; the stand-in keeps the last value.
   - `autoMergeRequest` on GitHub is null or an object whose `enabledBy` is an object; the
     stand-in writes `{"enabledBy": "lem"}`. The adapter types it `dict[str, object]` and reads
     only whether it is there, so no defect.
   - Not compared: what real `gh pr create` and `gh pr merge` print on stderr. The adapter keeps
     no log of a call, and the trial did not open or merge a second pull request to see it.
5. **The line of another `lem` names a folder of the Cellar.** Run d of S4 printed:
   `lem: /Users/Silver/.claude/plugins/cache/lem/lem/0.3.1/bin/lem comes first on PATH, and it is
   not Lem's command /opt/homebrew/Cellar/lem/0.3.1.2/libexec/bin/lem; the owner puts
   /opt/homebrew/Cellar/lem/0.3.1.2/libexec/bin before ... in his PATH`. That folder holds a
   version in its name, which the next upgrade removes, and the virtualenv's `python`,
   `python3`, `uvicorn`, `watchfiles` and `activate`, which would come first on his PATH too. It
   should name the folder Homebrew links `lem` into (`/opt/homebrew/bin`), or at least the
   `opt` path. Owner: `sessions` (`hooks/other.py`).
6. **The `next` of a brief names the bare command again.** After `lem land read SLUG` (17) the
   envelope's `next` is `lem land read SLUG`, not the form with `--record FILE`; after
   `lem land merge-review SLUG` (26) it is `lem land merge-review SLUG`, not the form with
   `--file FILE --tip TIP --base BASE`. An agent that follows `next` runs the brief again. It
   should name the record's form with its placeholders. Owner: `land-review` (`read`) and
   `land-merge` (`merge-review`).
7. **The pull request's text shows nothing for a silent check.** Its "Checks" part is
   `` - `sh tests/words.sh`: `` with nothing after the colon: the line takes the command's last
   line of output, which is empty when the command prints nothing (the log is
   `checks/r1-1-e3b0c44298fc.log`, the digest of no bytes). It should say the outcome (passed,
   exit 0) when there is no output. Owner: `land-propose` (`pr_text`).
8. **Smaller points of the envelopes.**
   - `land propose` (21) names no pull request: its result has `text`, `green` and `who_acts`,
     and the number and address are only in `task.json` (`landing.pull`). Owner: `land-propose`.
   - The `why` of `lem land next` before `merge` (28, 31) and after `read --record` (18) ends with
     "TITLE and SUBJECT are the report's commit subject, FILE the pull request's notes", which
     names placeholders its command does not have. Owner: `land-merge` (`next`).
   - The merge read's record keeps the reply's first line in `why`
     (`"why": "merge\n\nOne word ..."`). Owner: `land-merge`.
   - The merge agent's brief says "Read the pull request below" and holds the pull request's
     text, but neither its address nor the diff. Not checked against `main`'s brief. Owner:
     `land-merge` with `land-text`.
9. **`lem serve stop` cannot stop a server that `serve run --port N` started.** With no
   `machine.toml` in the trial's home, `lem serve stop` refused `owner-port` ("port 4536 is the
   owner's own board server's ...") while the trial's server ran on 59056: `stop` has no
   `--port` and reads only `[serve] port`. It stopped once `machine.toml` named 59056. The stop
   should find the server of its own home, by `serve.json` or a `--port`. Also `/api/server`
   gives `"url": "http://127.0.0.1:59056/"`, which answers 501 until `board-pages`, and no
   workspace address; the page was found at `/mac/repo/` from the routes. Owner: `board-service`
   (`cli/serve/stop.py`), and `board-pages` for `/`.
10. **gh writes its cache under the real home.** `~/.cache/gh/c6/86/101fd671...` was written at
    06:21:30, during `lem land merge`. That is gh's own cache, not a file of Lem; a trial that
    keeps the real `HOME` for gh's login leaves it. Owner: `pack-trial` and `trials` (their
    procedure), if a trial must leave nothing under the real home.
11. **Each landing command takes 1.5 to 3 seconds with no work to do.** `lem land next` took
    1.52 to 2.96 s, and a `not-due` refusal 1.55 to 2.43 s, also after the landing ended (37,
    38, 39): each reads origin over the network first. On the fast track an agent runs
    `land next` before each of about 12 steps. Not a defect by the plan's words; a cost to
    weigh. Owner: `land-merge` (`next`).
12. **Not checked against the plan's words: the agent's `PATH`.** The plan wants the formula's
    commands first on the session's `PATH` in S4 and S5. Run e of S4 did that with `T/bin`; S5
    had no session, so its `PATH` was `T/bin:/usr/bin:/bin` for every command.

## Timings

- S4, 20 runs of the manifest's line (`T/time_hook.py`, through `T/enter` and `/bin/sh -c`, so
  each run includes one `env -i` and two shells), load average `8.17 7.36 6.29` before and
  after:
  - no task: least 46.7 ms, median 48.8 ms, most 65.9 ms (`T/evidence/s4-timing-no-task.json`);
  - with `LEM_TASK`: least 48.6 ms, median 60.3 ms, most 119.3 ms
    (`T/evidence/s4-timing-task.json`).

  The plan's `hooks` suite asks a p95 of at most 55 ms; 20 runs give no p95, and the median
  with a task is over 55 ms at this load.
- The landing, each command's wall time from `T/evidence/*.meta` (load average at the end
  `5.31 5.90 5.93`): the commands with no network 0.09 to 0.17 s; `task worktree` 1.09 s;
  `land start` 2.18 s; `land base` 2.31 s; `land checks` 2.40 s; `land read` 2.21 s and its
  `--record` 2.52 s; `land propose` 8.18 s; `land merge-review` 2.46 s and its answer 2.38 s;
  `land merge` 11.84 s; `land merged` 3.62 s; `land clean` 5.40 s; `land next` 1.52 to 2.96 s.
  From `land start` to the end of `land clean`: 05:19:40 to 05:22:16 by the records, 2 min 36 s,
  with the trial's own pauses between commands in it.
- S6: the server listened 0.58 s after its start.

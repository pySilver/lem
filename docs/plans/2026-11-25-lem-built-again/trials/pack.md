# Packaging trials

The orchestrator runs this sheet. The owner supplies the trial tag, tap revision, Mac and GUI.
Use [the run order](run.md) for the folder, credentials, evidence and handoffs. Use a disposable
Homebrew installation on an Apple silicon test Mac or VM. `--skip-link` keeps `lem` out of
Homebrew's `bin`, but the install still changes its `opt/lem` link. Use a machine where that
change cannot replace the owner's app. Use the scratch home for every Claude Code command.

Set `TAG` to the approved tag, `VERSION` to `${TAG#v}`, and `COMMIT` to the commit the tag names.
Set `BREW` and `CLAUDE` to the absolute binaries of the trial machine. Set `KEG` to
`/opt/homebrew/opt/lem/libexec/bin`. Use a new name for each recorded step and keep its raw files
in `T/evidence`. Use the Python 3.14 executable `PY` from [the run order](run.md).

## Checks

- [x] P1 The formula and marketplace plugin install from one tag. **Owner for the tap and tag.**

  Passed on 2026-11-26 at 12:00 on the tag `v0.99.0` (`d60e2eb4`) and the local tap commit
  `9e789d6`: formula 0.99.0, `p1-release` exit 0, no linkage error, `/opt/homebrew/bin/lem`
  absent. `APP` is `/opt/homebrew/Cellar/lem/0.99.0/libexec/lib/python3.14/site-packages/lem/data`,
  `PLUGIN` is `/private/tmp/lem-trial-r1/home/.claude/plugins/cache/lem/lem/0.99.0`. The install
  ran with `umask 022` and `HOMEBREW_NO_INSTALL_UPGRADE=1`; its build dependency `uv` was linked
  into `/opt/homebrew/bin`, where it came before the owner's own uv, so it was unlinked
  (`p1-uv-unlink`). Evidence in `/private/tmp/lem-trial-r1/evidence/`: `p1-pre-*`, `p1-tag`,
  `p1-commit`, `p1-tap`, `p1-tap-rev`, `p1-archive-sha`, `p1-install`, `p1-formula`, `p1-version`,
  `p1-help`, `p1-market`, `p1-plugin`, `p1-plugins`, `p1-release`, `p1-unlinked`, `p1-keg-*`.

  In the disposable Homebrew installation, put the approved formula in `pySilver/tap`. Record
  its Git revision, formula, upstream URL, version, hash, and `uv.lock` build instruction.
  Keep the approved tag and commit with them. Use the tag's own marketplace index:

  ```sh
  "$T/step" p1-tag -- git clone --branch "$TAG" --depth 1 https://github.com/pySilver/lem.git "$T/source"
  "$T/step" --cwd source p1-commit -- git rev-parse HEAD
  "$T/step" p1-tap -- /usr/bin/env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW" cat pySilver/tap/lem
  "$T/step" p1-install -- /usr/bin/env HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 "$BREW" install --build-from-source --skip-link pySilver/tap/lem
  "$T/step" p1-formula -- "$BREW" list --versions pySilver/tap/lem
  "$T/step" --gui-path p1-version -- "$KEG/lem" version
  "$T/step" --gui-path p1-help -- "$KEG/lem" help
  "$T/step" p1-market -- "$CLAUDE" plugin marketplace add "$T/source"
  "$T/step" p1-plugin -- "$CLAUDE" plugin install lem@lem --scope user
  "$T/step" p1-plugins -- "$CLAUDE" plugin list --json
  ```

  If the tap is already present, use its approved checkout. Compare the commit in `p1-commit.out`
  with `COMMIT`. Only continue if the formula fetches the approved tag and builds with its lock.
  Record `APP` as `root` from `p1-version.out`. Record `PLUGIN` as the installed `lem@lem` plugin
  path from `p1-plugins.out`. Require `PLUGIN` under `T/home`. Use the following command to check
  the index and the two copies of the plugin. `PLUGIN` must be the installed plugin path.

  ```sh
  "$T/step" p1-release -- "$PY" -I -B -c '
  import json, re, sys
  from pathlib import Path
  source, app, plugin = map(Path, sys.argv[1:4])
  tag, version, commit = sys.argv[4:7]
  metadata = ".claude-plugin/plugin.json"
  market = json.loads((source / ".claude-plugin/marketplace.json").read_bytes())
  (entry,) = market["plugins"]
  assert market["name"] == entry["name"] == "lem"
  assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) and tag == "v" + version
  assert entry["version"] == version
  assert entry["source"] == {"source": "github", "repo": "pySilver/lem", "ref": tag}
  version_line = json.loads((source.parent / "evidence/p1-version.out").read_bytes())
  assert version_line == {"root": str(app), "version": version, "commit": commit}
  for half in (source, app, plugin):
      manifest = json.loads((half / metadata).read_bytes())
      assert manifest["name"] == "lem" and manifest["version"] == version
  for group in ("skills", "agents", "hooks"):
      for path in (source / group).rglob("*"):
          if path.is_file():
              name = path.relative_to(source)
              assert (app / name).read_bytes() == path.read_bytes(), name
              assert (plugin / name).read_bytes() == path.read_bytes(), name
  assert (app / metadata).read_bytes() == (source / metadata).read_bytes()
  assert (plugin / metadata).read_bytes() == (source / metadata).read_bytes()
  for path in (source / "src/lem").rglob("*.py"):
      name = path.relative_to(source / "src/lem")
      assert (app.parent / name).read_bytes() == path.read_bytes(), name
  logos = ("assets/lem-mark.svg", "assets/lem-mark-night.svg")
  for name in logos:
      assert (app / name).read_bytes() == (source / name).read_bytes(), name
  assert (plugin / ".claude-plugin/marketplace.json").read_bytes() == (
      source / ".claude-plugin/marketplace.json"
  ).read_bytes()
  assert not (plugin / "bin").exists()
  assert not (plugin / "setup.sh").exists()
  print(json.dumps({"tag": tag, "version": version, "commit": commit}))
  ' "$T/source" "$APP" "$PLUGIN" "$TAG" "$VERSION" "$COMMIT"
  "$T/step" p1-unlinked -- /bin/sh -c 'test ! -e /opt/homebrew/bin/lem && test ! -L /opt/homebrew/bin/lem'
  ```

  Pass when all steps exit zero and the formula version equals `VERSION`. Check the install's
  stderr for a linkage error even if the keg exists. Keep the full install streams, the formula,
  the tag evidence and the plugin list. Keep the Homebrew installation and the plugin for P2–P6.

- [x] P2 The version line names the half behind. **Runs alone.**

  Passed on 2026-11-26 on a keg built from a local formula of `rebuild` at `b5b9b32c`, not the
  tag: `PLUGIN` was the keg's data folder, as P1's plugin was not installed. Evidence in
  `/private/tmp/lem-trial-r1/evidence/`: `p2-older-*`, `p2-newer-*`, `p2-older-plugin.json`,
  `p2-newer-plugin.json`, `p2-start.json`; the control frame in place of P3's is
  `p2-control-session-start`. Index: `/private/tmp/lem-trial-r1/index.json`.

  Make two disposable copies of `PLUGIN`. In `T/older` set the plugin manifest version to `0.0.1`.
  In `T/newer` set it to the candidate's numeric major version plus one, with minor and patch zero.
  Leave the installed copies alone. In `T/repo`, initialized from [the run order](run.md), run:

  ```sh
  "$T/step" --cwd repo p2-task -- lem task open pack-hook --ask 'Check the installed hook.'
  "$T/step" p2-copies -- "$PY" -I -B -c '
  import json, shutil, sys
  from pathlib import Path
  plugin, folder = map(Path, sys.argv[1:])
  for name in ("older", "newer"):
      copied = folder / name
      shutil.copytree(plugin, copied)
      path = copied / ".claude-plugin/plugin.json"
      manifest = json.loads(path.read_bytes())
      major = int(manifest["version"].split(".")[0])
      manifest["version"] = "0.0.1" if name == "older" else f"{major + 1}.0.0"
      path.write_text(json.dumps(manifest))
  ' "$PLUGIN" "$T"
  ```

  Create `T/tmp/start.json` with `hook_event_name: SessionStart`, `source: startup`, `cwd: T/repo`,
  `session_id: p2-hook`, and `transcript_path: T/tmp/p2.jsonl`. Use JSON strings and absolute paths.
  For each `HALF` in `older newer`, run these commands. Run every `p2-$HALF-$HOOK` step even after
  the expected app refusal:

  ```sh
  "$T/step" --cwd repo "p2-$HALF-app" -- /usr/bin/env LEM_PLUGIN_ROOT="$T/$HALF" "$KEG/lem" task list
  for HOOK in corrections serve session-start precompact stop; do
    "$T/step" --cwd repo --gui-path --stdin tmp/start.json "p2-$HALF-$HOOK" -- /usr/bin/env CLAUDE_PLUGIN_ROOT="$T/$HALF" LEM_TASK=pack-hook /bin/sh "$T/$HALF/hooks/run" "$HOOK"
  done
  ```

  Pass when the app exits 1 with refusal `version` both ways. `session-start` must return one
  `systemMessage` line with the same update command as the app. Expect `claude plugin update lem@lem`
  for `older` and `brew upgrade pySilver/tap/lem` for `newer`. The other hooks exit zero with empty
  streams. Neither mismatch adds a session frame. Keep the two manifests, the input and the raw
  steps. Keep the matching-version frame from P3 as the control.

- [x] P3 A Claude Code session from the GUI reaches the installed hook. **Owner at the Mac.**

  Passed on 2026-11-26 at 12:03, run by the agent in an agterm pane (the owner's choice): the Bash
  tool saw `PATH` `/usr/bin:/bin` and `LEM_PLUGIN_ROOT` the P1 plugin, `LEM_HOOK_BIN` unset, no
  `--plugin-dir`; the frame `startup`, `98becc0c-7a91-415e-840a-4ff9ccbeb30e`, `pack-hook`. macOS
  `printenv` prints only its first name, so the sheet's `printenv PATH LEM_PLUGIN_ROOT` shows `PATH`
  alone: each name was asked in its own command. Evidence in `/private/tmp/lem-trial-r1/evidence/`: `p3-pane.txt`,
  `p3-sessions.jsonl`, `p3-session-env.sh`, `p3-process.txt`, `p3-process-env.txt`, `p3-probe-*`.

  Open the disposable agterm profile with the GUI. Run the following command from a new pane in
  `T/repo`. Enter the absolute values of the variables from this sheet in that pane.

  ```sh
  "$T/enter-gui" /usr/bin/env LEM_TASK=pack-hook "$CLAUDE"
  ```

  Use the plugin from P1. In Claude Code, ask it to run `/usr/bin/printenv PATH LEM_PLUGIN_ROOT`
  with the Bash tool. Capture the pane, the command result and
  `T/repo/.lem/state/tasks/pack-hook/sessions.jsonl`. Pass when the Bash tool sees
  `/usr/bin:/bin` and the P1 plugin path, and a new `startup` frame names this Claude Code session
  and `pack-hook`. Confirm neither `LEM_HOOK_BIN` nor a plugin directory argument supplied the
  hook. Close only this scratch pane before P4.

- [x] P4 Each installed hook line meets the time limit. **Runs alone on a quiet Mac.**

  Passed on 2026-11-26 at 10:36 on the local keg of `rebuild` at `b5b9b32c`, `PLUGIN` the keg's
  data folder: `ok: true`, load 3.79 before and 3.89 after, 30 frames, p95 per selector
  42.1, 41.2, 40.9, 41.2 and 42.5 ms (corrections, serve, session-start, precompact, stop).
  Evidence in `/private/tmp/lem-trial-r1/evidence/`: `p4-timing-quiet`, the manifest
  `p4-hooks.json` and `p4-hooks-run`; the refused attempt at load 5.19 `p4-timing-attempt1`, and
  a measurement at load 4.9 with the load gate lifted, `p4-timing-highload` (every p95 at most
  50.5 ms).

  ```sh
  "$T/step" p4-timing -- "$T/p95" --repo "$T/repo" --plugin "$PLUGIN" --task pack-hook
  ```

  The meter runs the installed manifest lines under the GUI `PATH`, with automatic serve off and
  no correction queue or waiting card. The `hooks` level's `test_cost.py` supplies the sample count
  of 30 and the quiet load limit of 4.0. The design's part 5 sets the 55 ms limit. Pass when the
  meter returns `ok: true`: the p95 of each selector is at most 55 ms, the Mac is within the load
  limit before and after, and the SessionStart frames and PreCompact text prove the hook ran.
  Keep the JSON with all samples, the manifest, start and end load and the measured hook path.
  Keep a high-load run as evidence of that attempt. Choose a new step name for the quiet run.

- [x] P5 The installed app's `lem doctor` finds every required row. **Runs alone with the trial profile ready.**

  Passed on 2026-11-26 at 12:00 on the P1 keg and plugin: 18 required rows found, the same names as
  the `REQUIRED` rows of the tag's `src/lem/cli/doctor/` (the Jev key is required only with the
  correction queue on); versions, `hooks/run` and PATH rows name the keg and `PLUGIN`. Evidence in
  `/private/tmp/lem-trial-r1/evidence/`: `p5-doctor-r3`, `p5-required-r3`.

  Put the absolute trial tools in `T/bin`. Install the required Claude Code skills or copy their
  approved files to the disposable home. Run with `lem` and `lem-hook` from `KEG` in `T/bin`.

  ```sh
  "$T/step" --cwd repo p5-doctor -- /usr/bin/env LEM_PLUGIN_ROOT="$PLUGIN" lem doctor
  "$T/step" p5-required -- "$PY" -I -B -c '
  import json, sys
  from pathlib import Path
  report = json.loads(Path(sys.argv[1]).read_bytes())
  required = [row for row in report["result"]["rows"] if row["need"] == "required"]
  assert report["ok"] and report["result"]["ok"] and required
  assert all(row["found"] for row in required)
  print(json.dumps([row["name"] for row in required]))
  ' "$T/evidence/p5-doctor.out"
  ```

  Compare the required names with the rows from the candidate's `src/lem/cli/doctor/` module.
  Confirm the versions, PATH and launcher rows point to the P1 halves. Keep the whole doctor
  result, including optional rows. Leave the read rule absent until P6.

- [x] P6 The first read prompts and the allow rule covers the next session. **Owner at the Mac.**

  Passed on 2026-11-26 at 12:05, run by the agent in agterm panes (the owner's choice): the first
  read asked "Do you want to proceed?" and option 1 allowed it once; with
  `Read(//opt/homebrew/Cellar/lem/**)` in `T/home/.claude/settings.json` the second session read
  `stages/new.md` with no prompt; `p6-doctor` finds the rule. Evidence in `/private/tmp/lem-trial-r1/evidence/`:
  `p6-first-prompt.txt`, `p6-first-read.txt`, `p6-second-read.txt`, `p6-rule.txt`, `p6-doctor`,
  `p6-doctor-row.json`.

  From `T/repo`, open a fresh Claude Code pane with `"$T/enter" "$CLAUDE" --permission-mode default`.
  Ask it to use the Read tool on `APP/skills/lem/SKILL.md`. Capture the outside-directory prompt.
  Select the one-time allow and record the successful read. Close the scratch pane. Copy the line
  from the `reads of Lem's files` row of `p5-doctor.out` into `permissions.allow` in
  `T/home/.claude/settings.json`. Expect `Read(//opt/homebrew/Cellar/lem/**)` for this keg. Use a
  fresh pane with the same launch command. Ask it to read `APP/skills/lem/stages/new.md` with Read.
  Pass when Claude Code reads the second file without the prompt and a repeat of `p5-doctor` shows
  the rule found in the scratch settings. Keep both pane captures, the rule and the doctor row.

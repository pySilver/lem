#!/usr/bin/env bash
# gate's shadow log, offline: gate-log.py records the judge's verdict and the user's answer
# in the git directory (never the work tree), refuses an unknown verdict and an answer to a
# question it never logged, and reports both side by side. Then panel's cast.py: the cast
# comes from the project alone (none there means no panel; the user's and the built-in cast only start one), a checkout older than its default
# branch's cast reads that cast, the project's profile comes from the checkout or the default branch
# and never from a generic layer, init copies a cast down, and run-dir makes a folder git ignores.
set -euo pipefail

cd "$(dirname "$0")/.."
LOG=$PWD/skills/lem-gate/scripts/gate-log.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
git -C "$WORK" init -q

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
gate() { "$PY" -B "$LOG" "$@" --repo "$WORK"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }

gate ask --id 001-size --question "Which size?" --verdict held --cite "no ruling covers it"
gate ask --id 002-gmc --question "May an approved promotion be edited?" --verdict decided --cite "promotions-follow-merchant-center.md"
gate answer --id 002-gmc --answer "only the end time"
if [ -f "$WORK/.git/decide-gate.jsonl" ] && [ -z "$(git -C "$WORK" status --porcelain --untracked-files=all)" ]; then
  pass "the log lives in the git directory, not the work tree"
else
  fail "the log lives in the git directory, not the work tree"
fi
if [ "$(status_of gate ask --id 003 --question q --verdict maybe)" = 1 ]; then pass "an unknown verdict is refused"; else fail "an unknown verdict is refused"; fi
if [ "$(status_of gate answer --id 404 --answer x)" = 1 ]; then pass "an answer to a question never logged is refused"; else fail "an answer to a question never logged is refused"; fi
out=$(gate report)
if grep -q 'owner: only the end time' <<<"$out" && grep -q 'owner: (not answered yet)' <<<"$out" && grep -q '2 questions, 1 answered' <<<"$out"; then
  pass "the report puts each verdict beside its answer and counts them"
else
  fail "the report puts each verdict beside its answer: $out"
fi
dir=$(gate dir)
if [ "$dir" = "$WORK/.git/lem/questions" ] && [ -d "$dir" ] && [ "$(gate dir)" = "$dir" ] && [ -z "$(git -C "$WORK" status --porcelain --untracked-files=all)" ]; then
  pass "the folder for the question files is in the git directory, and the work tree stays clean"
else
  fail "the folder for the question files: $dir"
fi
git -C "$WORK" -c user.name=t -c user.email=t@t commit -q --allow-empty -m start
git -C "$WORK" worktree add -q "$WORK-wt" -b side
if [ "$("$PY" -B "$LOG" dir --repo "$WORK-wt")" = "$dir" ]; then pass "a worktree gets the same folder as its main checkout"; else fail "the question folder from a worktree"; fi
git -C "$WORK" worktree remove --force "$WORK-wt"
if [ -d "$(dirname "$LOG")/__pycache__" ]; then fail "the script left no __pycache__"; else pass "the script left no __pycache__"; fi

CAST=$PWD/skills/lem-panel/scripts/cast.py
PANEL=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK" "$PANEL"' EXIT
export HOME=$PANEL/home
mkdir -p "$HOME"
commit() { git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "$2"; }
cast() { "$PY" -B "$CAST" "$@"; }
layer_of() { cast --repo "$1" | "$PY" -c 'import json, sys; c = json.load(sys.stdin); print(c["layer"], len(c["personas"]))'; }

REPO=$PANEL/repo
git init -q -b main "$REPO"
commit "$REPO" "start"
git init -q --bare "$PANEL/origin.git"
git -C "$REPO" remote add origin "$PANEL/origin.git"
git -C "$REPO" push -q origin main
git -C "$REPO" remote set-head origin main
none=$(cast --repo "$REPO" 2>&1 || true)
if [ "$(status_of cast --repo "$REPO")" = 1 ] && grep -q "this project has no personas in .lem/personas, so its setup is not finished and no panel can run" <<<"$none" \
  && grep -q "./lem init. writes them" <<<"$none" && grep -q "No generic cast answers in their place" <<<"$none"; then
  pass "a project with no personas has a setup that is not finished: the cast is refused with the step that writes them, and no generic cast answers"
else
  fail "no personas: $none"
fi
profile_of() { cast --repo "$1" | "$PY" -c 'import json, sys; p = json.load(sys.stdin)["profile"]; print("none" if p is None else p["source"].split(" at ")[0])'; }

mkdir -p "$HOME/.config/personas/cast"
printf '# Index\n' >"$HOME/.config/personas/cast/README.md"
printf '# Reader\n' >"$HOME/.config/personas/cast/reader.md"
if [ "$(status_of cast --repo "$REPO")" = 1 ]; then pass "the user's own cast answers no panel in a project that has no personas"; else fail "the user's cast ran a panel: $(layer_of "$REPO")"; fi
mkdir -p "$REPO/.lem/personas" && printf '# Index\n' >"$REPO/.lem/personas/README.md"
if [ "$(status_of cast --repo "$REPO")" = 1 ]; then pass "an index with no persona file is not a cast"; else fail "an index alone counted as a cast"; fi
rm -r "$REPO/.lem"

git -C "$REPO" branch old
mkdir -p "$REPO/.lem/personas"
printf '# Shopper\n' >"$REPO/.lem/personas/shopper.md"
printf '# Merchant\n' >"$REPO/.lem/personas/merchant.md"
if [ "$(layer_of "$REPO")" = "project 2" ]; then pass "the project's own people are the cast, and nobody of the user's cast is beside them"; else fail "project layer: $(layer_of "$REPO")"; fi
if [ "$(profile_of "$REPO")" = "none" ]; then pass "a project with no profile gets none, never a generic one"; else fail "profile without one: $(profile_of "$REPO")"; fi
printf '# Profile\n' >"$REPO/.lem/profile.md"
if [ "$(profile_of "$REPO")" = "checkout" ]; then pass "the checkout's profile is read, beside the project's cast"; else fail "checkout profile: $(profile_of "$REPO")"; fi

# A project that keeps its people in a folder of its own: a worktree branched before the settings
# named it still finds them on the default branch, and init there does not start a second cast.
CUSTOM=$PANEL/custom
git init -q -b main "$CUSTOM" && commit "$CUSTOM" "start" && git -C "$CUSTOM" branch before-the-cast
mkdir -p "$CUSTOM/.lem" "$CUSTOM/people" && printf '%s\n' '[paths]' 'personas = "people"' 'profile = "people/about.md"' '[branch]' 'base = "main"' > "$CUSTOM/.lem/project.toml"
printf '# Shopper\n' > "$CUSTOM/people/shopper.md" && printf '# About\n' > "$CUSTOM/people/about.md"
git -C "$CUSTOM" add -A && commit "$CUSTOM" "feat: the people of this project"
git -C "$CUSTOM" worktree add -q "$PANEL/custom-old" before-the-cast
refusal=$(cast init --repo "$PANEL/custom-old" 2>&1 || true)
if [ "$(layer_of "$CUSTOM")" = "project 2" ] && [ "$(layer_of "$PANEL/custom-old")" = "project 2" ] && [ "$(profile_of "$PANEL/custom-old")" = "main" ] \
  && [ "$(status_of cast init --repo "$PANEL/custom-old")" = 1 ] && grep -q 'rebase onto it' <<<"$refusal" && [ ! -e "$PANEL/custom-old/.lem" ]; then
  pass "a worktree older than the settings finds the cast and the profile where the default branch's settings keep them, and init does not start a second cast there"
else
  fail "a custom personas path from an older worktree: $(layer_of "$CUSTOM") / $(layer_of "$PANEL/custom-old") / $(profile_of "$PANEL/custom-old") / $refusal"
fi
# The same with settings written another way that TOML allows, and then with the paths taken out
# again: the default branch's own settings decide, not what the older worktree was told.
printf '%s\n' "[paths] # where things are" "  personas = 'people'" "  profile = 'people/about.md'" '[branch]' 'base = "main"' > "$CUSTOM/.lem/project.toml"
git -C "$CUSTOM" add -A && commit "$CUSTOM" "chore: the same settings, written another way"
quoted="$(layer_of "$PANEL/custom-old") $(profile_of "$PANEL/custom-old")"
mkdir -p "$PANEL/custom-old/.lem" && printf '%s\n' '[paths]' 'personas = "people"' 'profile = "people/about.md"' > "$PANEL/custom-old/.lem/project.toml"
printf '%s\n' '[branch]' 'base = "main"' > "$CUSTOM/.lem/project.toml" && mkdir -p "$CUSTOM/.lem/personas"
git -C "$CUSTOM" mv people/shopper.md .lem/personas/shopper.md && git -C "$CUSTOM" mv people/about.md .lem/profile.md && git -C "$CUSTOM" add -A && commit "$CUSTOM" "chore: Lem's own layout"
if [ "$quoted" = "project 2 main" ] && [ "$(layer_of "$PANEL/custom-old")" = "project 1" ] && [ "$(profile_of "$PANEL/custom-old")" = "main" ]; then
  pass "the default branch's settings are read as TOML, whatever their quotes and spaces, and a path they no longer name is Lem's own, also for a worktree that still names the old one"
else
  fail "the default branch's settings from an older worktree: $quoted / $(layer_of "$PANEL/custom-old") / $(profile_of "$PANEL/custom-old")"
fi

# The cast lands on local main only; origin/HEAD still names a main without it.
git -C "$REPO" add .lem
commit "$REPO" "cast"
git -C "$REPO" worktree add -q "$PANEL/old" old
source_of() { cast --repo "$1" | "$PY" -c 'import json, sys; c = json.load(sys.stdin); print(c["layer"], c["source"].split(" at ")[0], len(c["personas"]))'; }
if [ "$(source_of "$PANEL/old")" = "project main 2" ] && [ ! -e "$PANEL/old/.lem" ]; then
  pass "a worktree older than the cast reads it from the local default branch before it is pushed"
  profile=$(cast --repo "$PANEL/old" | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["profile"]["path"])')
  if [ "$(profile_of "$PANEL/old")" = "main" ] && grep -q '^# Profile$' "$profile"; then
    pass "the same worktree reads the default branch's profile"
  else
    fail "stale worktree profile: $(profile_of "$PANEL/old")"
  fi
else
  fail "stale worktree, cast unpushed: $(source_of "$PANEL/old")"
fi
git -C "$REPO" push -q origin main
if [ "$(source_of "$PANEL/old")" = "project main 2" ] && [ -z "$(git -C "$PANEL/old" status --porcelain --untracked-files=all)" ]; then
  pass "after the push it still reads the default branch's cast, and leaves the worktree clean"
else
  fail "stale worktree, cast pushed: $(source_of "$PANEL/old")"
fi
git -C "$REPO" branch -q -m main trunk
git -C "$REPO" remote set-head origin -d
git -C "$REPO" push -q origin trunk
git -C "$REPO" push -q origin --delete main
git -C "$REPO" fetch -q --prune origin
if [ "$(source_of "$PANEL/old")" = "project trunk 2" ]; then pass "a default branch named trunk is found without origin/HEAD"; else fail "trunk: $(source_of "$PANEL/old")"; fi

# A persona edit lands on the remote from another clone; the local branch is left behind.
git clone -q -b trunk "$PANEL/origin.git" "$PANEL/other"
printf '# Shopper, edited\n' >"$PANEL/other/.lem/personas/shopper.md"
git -C "$PANEL/other" add .lem
commit "$PANEL/other" "edit shopper"
git -C "$PANEL/other" push -q origin trunk
git -C "$REPO" fetch -q origin
shopper=$(cast --repo "$PANEL/old" | "$PY" -c 'import json, sys; print([p["path"] for p in json.load(sys.stdin)["personas"] if p["stem"] == "shopper"][0])')
if [ "$(source_of "$PANEL/old")" = "project origin/trunk 2" ] && grep -q 'edited' "$shopper"; then
  pass "when the local default branch is behind the remote one, the remote's newer cast is read"
else
  fail "local behind remote: $(source_of "$PANEL/old"), $(head -1 "$shopper")"
fi
copies=$(find "$REPO/.git/personas-profile" -name '*.md' | wc -l | tr -d ' ')
if [ "$copies" = 1 ]; then pass "commits that leave the profile unchanged share one copy of it"; else fail "profile copies: $copies"; fi
refusal=$(cast init --repo "$PANEL/old" 2>&1 || true)
if [ "$(status_of cast init --repo "$PANEL/old")" = 1 ] && grep -q 'rebase onto it' <<<"$refusal"; then
  pass "init refuses a worktree whose default branch already has a cast"
else
  fail "init in a stale worktree: $refusal"
fi
# A worktree branched after the cast landed holds its own copy; the remote has a newer shopper.
git -C "$REPO" worktree add -q -b newer "$PANEL/newer" trunk
newer_shopper=$(cast --repo "$PANEL/newer" | "$PY" -c 'import json, sys; print([p["path"] for p in json.load(sys.stdin)["personas"] if p["stem"] == "shopper"][0])')
if [ "$(source_of "$PANEL/newer")" = "project origin/trunk 2" ] && grep -q 'edited' "$newer_shopper" && [ "$(profile_of "$PANEL/newer")" = "checkout" ]; then
  pass "a worktree holding an unchanged older cast reads the default branch's newer one; an unchanged profile reads its own"
else
  fail "older copy: $(source_of "$PANEL/newer"), profile $(profile_of "$PANEL/newer")"
fi
printf '# Shopper, this branch\n' >"$PANEL/newer/.lem/personas/shopper.md"
if [ "$(source_of "$PANEL/newer")" = "project checkout 2" ]; then pass "a branch that edits its cast keeps its own"; else fail "edited cast: $(source_of "$PANEL/newer")"; fi
git -C "$PANEL/newer" checkout -q -- .lem
printf '# Profile, with versions\n' >"$PANEL/other/.lem/profile.md"
git -C "$PANEL/other" add .lem
commit "$PANEL/other" "profile versions"
git -C "$PANEL/other" push -q origin trunk
git -C "$REPO" fetch -q origin
newer_profile=$(cast --repo "$PANEL/newer" | "$PY" -c 'import json, sys; print(json.load(sys.stdin)["profile"]["path"])')
if [ "$(profile_of "$PANEL/newer")" = "origin/trunk" ] && grep -q 'with versions' "$newer_profile" && [ -z "$(git -C "$PANEL/newer" status --porcelain --untracked-files=all)" ]; then
  pass "an edit to the profile on the default branch reaches a worktree without a merge, and leaves it clean"
else
  fail "newer profile: $(profile_of "$PANEL/newer")"
fi

if [ "$(status_of cast --repo "$PANEL/no-such-dir")" = 1 ]; then pass "a --repo that does not exist is refused"; else fail "a missing --repo was accepted"; fi

FRESH=$PANEL/fresh
git init -q -b main "$FRESH"
cast init --repo "$FRESH" >/dev/null
if [ -f "$FRESH/.lem/personas/reader.md" ] && [ -f "$FRESH/.lem/personas/README.md" ] && [ "$(layer_of "$FRESH")" = "project 1" ]; then
  pass "init copies a starting cast, the user's before the built-in one, into the project"
else
  fail "init did not copy the resolved cast"
fi
if [ "$(status_of cast init --repo "$FRESH")" = 1 ]; then pass "init refuses a project that already has a cast"; else fail "init overwrote a project cast"; fi
README_ONLY=$PANEL/readme-only
git init -q -b main "$README_ONLY"
mkdir -p "$README_ONLY/.lem/personas"
printf '# Ours\n' >"$README_ONLY/.lem/personas/README.md"
if [ "$(status_of cast init --repo "$README_ONLY")" = 1 ] && grep -q '^# Ours$' "$README_ONLY/.lem/personas/README.md"; then
  pass "init refuses a cast folder that holds only an index, and leaves it as it was"
else
  fail "init overwrote an index"
fi

# the day before the folder is made and after it: a folder made at midnight is named for one of the two
day_from=$(date +%Y-%m-%d)
dir=$(cast run-dir pack-size --repo "$REPO")
day_to=$(date +%Y-%m-%d)
if [ -d "$dir" ] && { [ "$(basename "$dir")" = "$day_from-pack-size" ] || [ "$(basename "$dir")" = "$day_to-pack-size" ]; } && [ -z "$(git -C "$REPO" status --porcelain --untracked-files=all)" ]; then
  pass "run-dir makes a dated folder that git status never shows"
else
  fail "run-dir: $dir; status: $(git -C "$REPO" status --porcelain --untracked-files=all)"
fi
if [ "$(status_of cast run-dir pack-size --repo "$REPO")" = 1 ]; then pass "run-dir refuses a folder that already exists"; else fail "run-dir reused a folder"; fi

# A project that keeps its cast where an older tool reads it says so in its settings.
LINKED=$PANEL/linked
git init -q -b main "$LINKED"
mkdir -p "$LINKED/.personas/cast" "$LINKED/.lem"
printf '# Shopper\n' > "$LINKED/.personas/cast/shopper.md"
printf '# Profile\n' > "$LINKED/.personas/profile.md"
printf '%s\n' '[paths]' 'personas = ".personas/cast"' 'profile = ".personas/profile.md"' > "$LINKED/.lem/project.toml"
linked=$(cast --repo "$LINKED")
if [ "$("$PY" -c 'import json, sys; c = json.load(sys.stdin); print(c["layer"], c["dir"], c["profile"]["path"])' <<<"$linked")" = "project $LINKED/.personas/cast $LINKED/.personas/profile.md" ]; then
  pass "a cast and a profile at the paths the project's settings name are the project's"
else
  fail "linked cast: $linked"
fi
dir=$(cast run-dir linked-run --repo "$LINKED")
if [ "$(dirname "$dir")" = "$LINKED/.personas/runs" ]; then pass "a linked cast's panels write beside it"; else fail "linked run-dir: $dir"; fi
printf '%s\n' '[paths]' 'persona = "x"' > "$LINKED/.lem/project.toml"
if [ "$(status_of cast --repo "$LINKED")" = 1 ]; then pass "a settings file Lem refuses stops the panel too"; else fail "bad settings passed"; fi
if [ -d "$(dirname "$CAST")/__pycache__" ]; then fail "cast.py left no __pycache__"; else pass "cast.py left no __pycache__"; fi

[ "$fails" -eq 0 ] || { printf '%d failure(s)\n' "$fails"; exit 1; }

#!/usr/bin/env bash
# The persona panel's cast.py, offline: the cast
# comes from the project alone (none there means no panel; the user's and the built-in cast only start one), a checkout older than its default
# branch's cast reads that cast, the project's profile comes from the checkout or the default branch
# and never from a generic layer, init copies a cast down, and run-dir makes a folder in Lem's state folder.
set -eEuo pipefail

cd "$(dirname "$0")/.."
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh
collected
WORK=$(cd "$(mktemp -d)" && pwd -P)
export XDG_CONFIG_HOME="$WORK/config"  # the owner's status (`lem_state.owner_mark`) of this run, never the home directory's
trap 'stopped; rm -rf "$WORK" "$WORK-wt"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
git -C "$WORK" init -q

status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }

CAST=$PWD/skills/lem-panel/scripts/cast.py
PANEL=$(cd "$(mktemp -d)" && pwd -P)
trap 'stopped; rm -rf "$WORK" "$WORK-wt" "$PANEL"' EXIT
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

# A persona's file names its seats in a frontmatter, which its agent does not read; a file with none answers on the panel's two seats.
SEATED=$PANEL/seated
git init -q -b main "$SEATED" && mkdir -p "$SEATED/.lem/personas"
printf '%s\n' '---' 'seats: ["claude/opus:high", "claude/fable:max"]' '---' '# Clerk' '' 'Counts the till.' >"$SEATED/.lem/personas/clerk.md"
printf '# Owner\n' >"$SEATED/.lem/personas/owner.md"
seated=$(cast --repo "$SEATED" | "$PY" -c '
import json, pathlib, sys
c = {p["stem"]: p for p in json.load(sys.stdin)["personas"]}
clerk, owner = c["clerk"], c["owner"]
print([s["seat"] for s in clerk["seats"]], clerk["seats_from"], pathlib.Path(clerk["person"]).read_text(), owner["person"] == owner["path"],
      owner["seats_from"], sorted(s["name"] for s in owner["seats"] + owner["left_out"]))' 2>&1 || true)
printf '%s\n' '---' 'seats: ["gemini/pro:high"]' '---' '# Clerk' >"$SEATED/.lem/personas/clerk.md"
wrong=$(cast --repo "$SEATED" 2>&1 || true)
if [ "$seated" = "['claude/opus:high', 'claude/fable:max'] file # Clerk

Counts the till.
 True default ['opus', 'sol']" ] && [ "$(status_of cast --repo "$SEATED")" = 1 ] && grep -qF "$SEATED/.lem/personas/clerk.md: seats[0] = 'gemini/pro:high'" <<<"$wrong" \
  && grep -qF 'seats: ["claude/opus:high", "codex/gpt-6.2-sol:high"]' <<<"$wrong"; then
  pass "a persona's frontmatter names its seats and its agent reads the file without it; a file with none answers on Opus and Sol; a seat the settings would refuse stops the cast with the file and the line to write"
else
  fail "a persona's seats: $seated / $wrong"
fi

# A worktree branched before the cast still finds the cast and the profile on the default branch, in
# their one place, and init there does not start a second cast.
CUSTOM=$PANEL/custom
git init -q -b main "$CUSTOM" && commit "$CUSTOM" "start" && git -C "$CUSTOM" branch before-the-cast
mkdir -p "$CUSTOM/.lem/personas" && printf '%s\n' '[branch]' 'base = "main"' > "$CUSTOM/.lem/settings.toml"
printf '# Shopper\n' > "$CUSTOM/.lem/personas/shopper.md" && printf '# About\n' > "$CUSTOM/.lem/profile.md"
git -C "$CUSTOM" add -A && commit "$CUSTOM" "feat: the people of this project"
git -C "$CUSTOM" worktree add -q "$PANEL/custom-old" before-the-cast
refusal=$(cast init --repo "$PANEL/custom-old" 2>&1 || true)
if [ "$(layer_of "$CUSTOM")" = "project 1" ] && [ "$(layer_of "$PANEL/custom-old")" = "project 1" ] && [ "$(profile_of "$PANEL/custom-old")" = "main" ] \
  && [ "$(status_of cast init --repo "$PANEL/custom-old")" = 1 ] && grep -q 'rebase onto it' <<<"$refusal" && [ ! -e "$PANEL/custom-old/.lem" ]; then
  pass "a worktree older than the cast finds the cast and the profile on the default branch, and init does not start a second cast there"
else
  fail "the cast from an older worktree: $(layer_of "$CUSTOM") / $(layer_of "$PANEL/custom-old") / $(profile_of "$PANEL/custom-old") / $refusal"
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
copies=$(find "$REPO/.lem/state/personas-profile" -name '*.md' 2>/dev/null | wc -l | tr -d ' ' || true)
ingit=$(find "$REPO/.git" -maxdepth 1 -name 'personas-*' | wc -l | tr -d ' ')
if [ "$copies" = 1 ] && [ "$ingit" = 0 ] && [ -d "$REPO/.lem/state/personas-cast" ]; then
  pass "commits that leave the profile unchanged share one copy of it, and the copies are in Lem's state folder, none in the git directory"
else
  fail "profile copies: $copies, in the git directory: $ingit"
fi
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
if [ -d "$dir" ] && [ "$(dirname "$dir")" = "$REPO/.lem/state/panels" ] && { [ "$(basename "$dir")" = "$day_from-pack-size" ] || [ "$(basename "$dir")" = "$day_to-pack-size" ]; } \
  && [ -z "$(git -C "$REPO" status --porcelain --untracked-files=all)" ] && [ ! -e "$REPO/.lem/runs" ]; then
  pass "run-dir makes a dated folder in Lem's state folder, panels/, that git status never shows"
else
  fail "run-dir: $dir; status: $(git -C "$REPO" status --porcelain --untracked-files=all)"
fi
if [ "$(status_of cast run-dir pack-size --repo "$REPO")" = 1 ]; then pass "run-dir refuses a folder that already exists"; else fail "run-dir reused a folder"; fi
# from a worktree the folder is the main checkout's, and in a repository new to Lem git shows nothing of it
from_worktree=$(cast run-dir from-a-worktree --repo "$PANEL/old")
NEW_TO_LEM=$PANEL/new-to-lem
git init -q -b main "$NEW_TO_LEM"
new_dir=$(cast run-dir first-panel --repo "$NEW_TO_LEM")
if [ "$(dirname "$from_worktree")" = "$REPO/.lem/state/panels" ] && [ ! -e "$PANEL/old/.lem/state" ] \
  && [ "$(dirname "$new_dir")" = "$NEW_TO_LEM/.lem/state/panels" ] && [ -z "$(git -C "$NEW_TO_LEM" status --porcelain --untracked-files=all)" ]; then
  pass "run-dir in a worktree makes the folder in the main checkout's state folder, and in a repository new to Lem git status shows nothing"
else
  fail "run-dir from a worktree: $from_worktree; in a new repository: $new_dir, status: $(git -C "$NEW_TO_LEM" status --porcelain --untracked-files=all)"
fi

# A settings file Lem refuses stops the panel too.
LINKED=$PANEL/linked
git init -q -b main "$LINKED"
mkdir -p "$LINKED/.lem"
printf '%s\n' '[paths]' 'persona = "x"' > "$LINKED/.lem/settings.toml"
if [ "$(status_of cast --repo "$LINKED")" = 1 ]; then pass "a settings file Lem refuses stops the panel too"; else fail "bad settings passed"; fi
# once without -B: whatever the run says, its imports wrote no bytecode
env -u PYTHONDONTWRITEBYTECODE "$PY" "$CAST" --repo "$LINKED" >/dev/null 2>&1 || true
if [ -d "$(dirname "$CAST")/__pycache__" ] || [ -d skills/lem/scripts/__pycache__ ]; then fail "cast.py left no __pycache__"; else pass "cast.py left no __pycache__"; fi

# Every skill Lem ships starts only for Lem: the flag keeps it out of every session's list of
# skills, and its description is short and names Lem. The `lem` skill itself keeps its own.
shipped=$("$PY" -c '
import json, pathlib, sys
wrong = []
for path in sorted(pathlib.Path("skills").glob("*/SKILL.md")):
    head = path.read_text(encoding="utf-8").split("\n---\n", 1)[0].splitlines()[1:]
    flag = "disable-model-invocation: true" in head
    line = next((l for l in head if l.startswith("description:")), "description: ")
    text = line[len("description:"):].strip()
    text = json.loads(text) if text.startswith("\"") else text
    name = path.parent.name
    if name == "lem":
        if flag: wrong.append("lem has the flag")
        continue
    if not flag: wrong.append(f"{name} has no flag")
    if len(text) >= 300 or text in (">", "|"): wrong.append(f"{name} has a description of {len(text)} characters")
    if "Lem" not in text: wrong.append(f"{name} names no Lem")
print("; ".join(wrong) or "yes")
')
if [ "$shipped" = yes ]; then
  pass "every shipped skill has disable-model-invocation and a description under 300 characters that names Lem, and the lem skill has no flag"
else
  fail "the shipped skills' frontmatter: $shipped"
fi

results_add_up
finished=yes
[ "$fails" -eq 0 ] || { printf '%d failure(s)\n' "$fails"; exit 1; }
printf 'all passed\n'

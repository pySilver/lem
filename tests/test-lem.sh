#!/usr/bin/env bash
# Lem's project settings, offline: project.py resolves where a repository keeps what
# the skill reads. With no settings file it answers from the skill's own layout; init points at the
# folders an older tool already reads instead of moving them; a settings file with an unknown key,
# a wrong value or a path that leaves the repository is refused; careful names the files a
# project's careful patterns match.
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT=$PWD/skills/lem/scripts/project.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
project() { "$PY" -B "$PROJECT" "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }

NEW=$WORK/new
git init -q -b main "$NEW"
out=$(project --repo "$NEW" show)
if [ "$(field 'd["settings"]' <<<"$out")" = "None" ] && [ "$(field 'd["paths"]["styleguide"]["path"]' <<<"$out")" = "$NEW/.lem/styleguide" ] \
  && [ "$(field 'd["branch"]["land"]' <<<"$out")" = "owner" ]; then
  pass "with no settings file, show answers from the skill's own layout and the owner lands"
else
  fail "defaults: $out"
fi
if [ "$(status_of project --repo "$NEW" init)" = 1 ]; then pass "init refuses a checkout whose base branch it cannot tell"; else fail "init without a base"; fi
project --repo "$NEW" init --base main --reviewer codex >/dev/null
out=$(project --repo "$NEW" show)
if [ "$(field 'd["branch"]["base"]' <<<"$out")" = "main" ] && [ "$(field 'd["paths"]["personas"]["path"]' <<<"$out")" = "$NEW/.lem/personas" ] \
  && [ "$(field 'd["seats"]["reviewer"]' <<<"$out")" = "codex" ]; then
  pass "init in a new project writes the skill's own layout, the given base and the reviewer seat"
else
  fail "init in a new project: $out"
fi
if [ "$(status_of project --repo "$NEW" init --base main)" = 1 ]; then pass "init refuses a settings file that already exists"; else fail "second init"; fi

OLD=$WORK/old
git init -q -b master "$OLD"
mkdir -p "$OLD/.claude/rules" "$OLD/.revmux" "$OLD/.personas/cast" "$OLD/docs/plans"
touch "$OLD/.personas/profile.md"
err=$(project --repo "$OLD" init --base master 2>&1 || true)
if [ "$(status_of project --repo "$OLD" init --base master)" = 1 ] && grep -q "styleguide in .claude/rules" <<<"$err" && [ ! -e "$OLD/.lem" ]; then
  pass "init refuses to choose between the folders already there and a new layout, and names them"
else
  fail "init without --existing: $err"
fi
if [ "$(project --repo "$OLD" existing | field 'sorted(d)')" = "['personas', 'profile', 'review', 'styleguide']" ]; then
  pass "existing lists the settings an older tool already keeps here"
else
  fail "existing: $(project --repo "$OLD" existing)"
fi
NEWLAYOUT=$WORK/newlayout
git init -q -b master "$NEWLAYOUT"
mkdir -p "$NEWLAYOUT/.claude/rules"
project --repo "$NEWLAYOUT" init --base master --existing new >/dev/null
if [ "$(project --repo "$NEWLAYOUT" path styleguide)" = "$NEWLAYOUT/.lem/styleguide" ]; then
  pass "init --existing new starts the skill's own layout beside the older folders"
else
  fail "init --existing new"
fi
project --repo "$OLD" init --base master --existing link >/dev/null
out=$(project --repo "$OLD" show)
if [ "$(field 'd["paths"]["styleguide"]["path"]' <<<"$out")" = "$OLD/.claude/rules" ] && [ "$(field 'd["paths"]["review"]["path"]' <<<"$out")" = "$OLD/.revmux" ] \
  && [ "$(field 'd["paths"]["personas"]["path"]' <<<"$out")" = "$OLD/.personas/cast" ] && [ "$(field 'd["paths"]["profile"]["exists"]' <<<"$out")" = "True" ] \
  && [ "$(field 'd["paths"]["lessons"]["exists"]' <<<"$out")" = "False" ]; then
  pass "init --existing link points at the folders an older tool already reads, and show says which paths exist"
else
  fail "init over older folders: $out"
fi
if [ "$(project --repo "$OLD/docs" path plans)" = "$OLD/docs/plans" ]; then pass "path prints one absolute path, from any directory of the checkout"; else fail "path plans"; fi
if [ "$(status_of project --repo "$OLD" path plan)" = 1 ]; then pass "an unknown path name is refused"; else fail "unknown path name"; fi

settings() { printf '%s\n' "$@" > "$OLD/.lem/project.toml"; }
settings '[branch]' 'base = "master"' 'lands = "agent"'
err=$(project --repo "$OLD" show 2>&1 || true)
if [ "$(status_of project --repo "$OLD" show)" = 1 ] && grep -q "did you mean 'land'" <<<"$err"; then pass "an unknown key is refused with the nearest valid one"; else fail "unknown key: $err"; fi
settings '[branch]' 'base = "master"' 'land = "robot"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a land value other than owner or agent is refused"; else fail "land value"; fi
settings '[paths]' 'styleguide = "../elsewhere"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a path that leaves the repository is refused"; else fail "path outside"; fi
settings '[gate]' 'commands = "pytest"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "gate commands that are not a list are refused"; else fail "gate type"; fi
settings '[seats]' 'reviewer = "gemini"'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a reviewer that is neither claude nor codex is refused"; else fail "reviewer value"; fi
settings '[seats]' 'reviewer = "claude"'
if [ "$(project --repo "$OLD" show | field 'd["seats"]["reviewer"]')" = "claude" ]; then pass "the reviewer seat may be the same family as the builder"; else fail "reviewer claude"; fi
settings '[branch]' 'base = "v2"' 'protected = ["master", "develop"]'
err=$(project --repo "$OLD" may-land master 2>&1 || true)
if [ "$(status_of project --repo "$OLD" may-land master)" = 1 ] && grep -q "protected" <<<"$err" && [ "$(status_of project --repo "$OLD" may-land feature)" = 1 ] \
  && [ "$(status_of project --repo "$OLD" may-land v2)" = 0 ]; then
  pass "may-land refuses a protected branch and any branch but the base, and accepts the base"
else
  fail "may-land: $err"
fi
settings '[branch]' 'base = "master"' 'protected = ["master"]'
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a base branch that is also protected is refused as a contradiction"; else fail "protected base"; fi
settings '[tools]' 'annotate = "my-own-rev"'
if [ "$(project --repo "$OLD" show | field 'd["tools"]["annotate"]')" = "my-own-rev" ]; then pass "a project names its own tool for marking up a plan"; else fail "tools.annotate"; fi
settings 'not toml ['
if [ "$(status_of project --repo "$OLD" show)" = 1 ]; then pass "a settings file that does not parse is refused"; else fail "parse error"; fi

settings '[branch]' 'base = "master"' '[flow]' 'careful = ["app/outbox/*", "*/migrations/*"]'
out=$(project --repo "$OLD" careful app/outbox/emit/site.py app/products/migrations/0002_x.py app/products/models.py "$OLD/app/outbox/a.py")
if [ "$(field 'sorted(c["file"] for c in d["careful"])' <<<"$out")" = "['app/outbox/a.py', 'app/outbox/emit/site.py', 'app/products/migrations/0002_x.py']" ] \
  && [ "$(field 'd["plain"]' <<<"$out")" = "['app/products/models.py']" ]; then
  pass "careful names the files a pattern matches, nested ones and absolute paths too"
else
  fail "careful: $out"
fi
if [ "$(status_of project --repo "$WORK" show)" = 1 ]; then pass "a directory outside any checkout is refused"; else fail "outside a checkout"; fi

# Task state: one directory per task inside the git directory, seen from every worktree.
commit() { git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "$2"; }
commit "$OLD" start
git -C "$OLD" worktree add -q "$WORK/wt" -b feat/x
dir=$(project --repo "$WORK/wt" task-dir report-dates-stay-whole)
if [ "$dir" = "$OLD/.git/lem/tasks/report-dates-stay-whole" ] && [ -d "$dir/reports" ] && [ -z "$(git -C "$WORK/wt" status --porcelain)" ]; then
  pass "task-dir, run in a worktree, makes the task's directory in the shared git directory"
else
  fail "task-dir: $dir"
fi
settings '[branch]' 'base = "master"'
where=$(project --repo "$OLD" worktree-dir report-dates-stay-whole)
if [ "$where" = "$OLD/.lem/worktrees/report-dates-stay-whole" ] && [ ! -e "$where" ] && [ -z "$(git -C "$OLD" status --porcelain -- .lem/worktrees)" ]; then
  pass "worktree-dir names a path under a folder git status never shows, and makes no worktree itself"
else
  fail "worktree-dir: $where / $(git -C "$OLD" status --porcelain -- .lem/worktrees)"
fi
if [ "$(project --repo "$WORK/wt" state-dir)" = "$OLD/.git/lem" ]; then pass "state-dir prints the one folder every worktree shares"; else fail "state-dir"; fi
if [ "$(status_of project --repo "$OLD" task-dir "Report Dates")" = 1 ]; then pass "a slug that is not hyphenated lower-case words is refused"; else fail "slug form"; fi
printf '%s\n' 'Keep report dates whole.' '' 'more' > "$dir/task.md"
printf '%s\n' '2026-01-02 build: task 2 of 3 running' 'next: land' '' '2026-01-01 plan written' > "$dir/state.md"
out=$(project --repo "$OLD" tasks)
if [ "$(field 'd[0]["ask"]' <<<"$out")" = "Keep report dates whole." ] && [ "$(field 'd[0]["state"].splitlines()[-1]' <<<"$out")" = "next: land" ] \
  && [ "$(field 'len(d)' <<<"$out")" = 1 ]; then
  pass "tasks lists each task with its ask and only the newest state block"
else
  fail "tasks: $out"
fi

# The review queue: a landing adds an item, high risk first, and an unread normal item expires.
QUEUE=$PWD/skills/lem/scripts/review_queue.py
queue() { "$PY" -B "$QUEUE" --repo "$OLD" "$@"; }
first=$(queue add report-dates --range abc..def --risk normal)
second=$("$PY" -B "$QUEUE" --repo "$WORK/wt" add auth-token-index --range def..123 --risk high --note "touches the token lookup")
out=$(queue list)
if [ "$first" = 1 ] && [ "$second" = 2 ] && [ "$(field '[i["id"] for i in d]' <<<"$out")" = "[2, 1]" ] && [ "$(field 'd[0]["due"]' <<<"$out")" = "today" ]; then
  pass "a landing from any worktree joins one queue, and a high item is listed first and due today"
else
  fail "queue order: $out"
fi
queue close 2 --outcome "fixed in token-index-added"
if [ "$(status_of queue close 2 --outcome again)" = 1 ] && [ "$(status_of queue close 9 --outcome x)" = 1 ]; then
  pass "closing an item twice, or one that does not exist, is refused"
else
  fail "close refusals"
fi
printf '%s\n' '{"id": 3, "slug": "old-normal", "range": "a..b", "risk": "normal", "note": null, "added": "2020-01-01T00:00:00+00:00", "outcome": null}' \
  '{"id": 4, "slug": "old-high", "range": "b..c", "risk": "high", "note": null, "added": "2020-01-01T00:00:00+00:00", "outcome": null}' >> "$OLD/.git/lem/review-queue.jsonl"
out=$(queue expire)
left=$(queue list)
if [ "$(field 'd["expired"]' <<<"$out")" = "[3]" ] && [ "$(field '[(i["id"], i["due"]) for i in d]' <<<"$left")" = "[(4, 'overdue'), (1, 'when the day allows')]" ]; then
  pass "expire closes an old normal item as not reviewed, and an old high item stays open and overdue"
else
  fail "expire: $out / $left"
fi

# The machine check: a required tool that is absent fails it, an optional one only changes its row.
DOCTOR=$PWD/skills/lem/scripts/doctor.py
BIN=$WORK/bin
FAKEHOME=$WORK/home
mkdir -p "$BIN" "$FAKEHOME"
ln -s "$(command -v git)" "$BIN/git"
fake() { printf '#!/bin/sh\necho "%s"\n' "$2" > "$BIN/$1"; chmod +x "$BIN/$1"; }
doctor() { env -i PATH="$BIN" HOME="$FAKEHOME" "$PY" -B "$DOCTOR"; }
row() { field "next(t for t in d[\"tools\"] if t[\"name\"] == \"$1\")[\"$2\"]"; }
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(field 'd["ok"]' <<<"$out")" = "False" ] && [ "$(row revmux found <<<"$out")" = "False" ] && [ "$(row git found <<<"$out")" = "True" ]; then
  pass "doctor exits 1 and says so when the review tool is absent"
else
  fail "doctor without revmux: $out"
fi
fake revmux "revmux v9.9.9"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row revmux detail <<<"$out")" = "revmux v9.9.9" ] && [ "$(row agterm found <<<"$out")" = "False" ] \
  && [ "$(field '[t["name"] for t in d["tools"] if t["name"] == "agterm skill"]' <<<"$out")" = "[]" ] && [ "$(row mailbox-chat need <<<"$out")" = "required" ]; then
  pass "the review tool alone is not enough: agterm and the mailbox are required, and there is no row for the agterm skill without agterm"
else
  fail "doctor with revmux only: $out"
fi
fake agtermctl "agtermctl 1.0"
fake mailbox-chat.py "mailbox-chat"
out=$(doctor || true)
if [ "$(status_of doctor)" = 1 ] && [ "$(row agterm found <<<"$out")" = "True" ] && [ "$(row agterm in_session <<<"$out")" = "False" ] && [ "$(row 'agterm skill' found <<<"$out")" = "False" ]; then
  pass "agterm without its skill fails the check, and a run outside agterm says it is not in a session"
else
  fail "doctor with agterm, no skill: $out"
fi
mkdir -p "$FAKEHOME/.agents/skills/agterm" "$FAKEHOME/.config/cronn"
touch "$FAKEHOME/.agents/skills/agterm/SKILL.md"
out=$(doctor)
if [ "$(field 'd["ok"]' <<<"$out")" = "True" ] && [ "$(row 'agterm skill' detail <<<"$out")" = "$FAKEHOME/.agents/skills/agterm" ] && [ "$(row cronn found <<<"$out")" = "False" ] \
  && [ "$(row plannotator found <<<"$out")" = "False" ] && [ "$(row plannotator need <<<"$out")" = "optional" ] && [ "$(row codex found <<<"$out")" = "False" ]; then
  pass "with git, the review tool, agterm, its skill and the mailbox the check passes, and absent optional tools only change their rows"
else
  fail "doctor with the required set: $out"
fi
printf 'CRONN_PORT=1\n' > "$FAKEHOME/.config/cronn/cronn.env"
fake cronn "cronn"
out=$(doctor)
if [ "$(row cronn found <<<"$out")" = "True" ] && [ "$(row cronn running <<<"$out")" = "False" ]; then
  pass "an installed cronn that does not answer is reported as not running"
else
  fail "doctor with cronn: $out"
fi
if [ -d "$(dirname "$PROJECT")/__pycache__" ]; then fail "the scripts left no __pycache__"; else pass "the scripts left no __pycache__"; fi

if [ "$fails" -gt 0 ]; then
  printf '\n%s check(s) failed\n' "$fails"
  exit 1
fi
printf '\nall checks passed\n'

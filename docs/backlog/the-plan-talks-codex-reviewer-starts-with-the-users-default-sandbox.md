---
worth: yes
where: skills/lem/harness/claude-code/second-opinion.md
added: 2026-11-21
---
# The plan talk's Codex reviewer starts with the user's default sandbox

The harness calls the `second-opinion` capability read-only (`harness/README.md`), and the headless
Codex calls of `ask-experts.md` and `ask-merger.md` pass `-s read-only`. The plan talk's reviewer
pane does not: `second-opinion.md`, step 2, types `codex "$(cat "PATH/prompts/reviewer.md")"`, so
Codex starts with the sandbox the user's configuration gives. On the owner's machine
`~/.codex/config.toml` sets no `sandbox_mode` and marks the Lem repository trusted (the second
reader's check, 2026-11-21). The only guard is the reviewer's brief, which says that the defender
is the only one that edits files.

A run, from reading (not run): a careful plan's talk, with `seats.reviewer = "codex/..."`. The
reviewer finds a wrong path in the plan and, in place of a message to the defender, fixes the
plan file itself, in the main checkout the pair stands in, where every task's worktree lives.

A bare `-s read-only` does not do: both reviewers probed it with the installed `codex-cli 0.169.0`.
Under `:read-only` the write of the reply file under `/private/tmp` failed (Astra), and `codex
sandbox -P :read-only` denied the scratch write and the socket (Sol). The reviewer replies through
`mailbox-chat.py say --file`, which needs that file, so the talk would stop.

The options:

- **A named Codex permission profile on the launch line**: read everything, write one reply file.
  Astra's line keeps the mailbox recipe's own reply path and needs no file of the user's changed:

  ```sh
  codex -C "$WORKTREE" \
    -c 'default_permissions="lem_review"' \
    -c "permissions.lem_review.filesystem={\":root\"=\"read\",\"/private/tmp/mailbox-chat-${AGTERM_PANE_ID:?}.txt\"=\"write\"}" \
    "$(cat "$SKILL_DIR/prompts/reviewer.md")"
  ```

  Costs nothing per task; the profile's form is Codex's and may change with it.
- **The same with one reply folder**, Sol's line, with a profile in a configuration file of the
  user's (`~/.codex/lem-plan-review.config.toml`, `":root" = "read"`, `"/private/tmp/lem-plan-replies"
  = "write"`) and `-a never`:

  ```sh
  codex -C "$REVIEW_REPO" -p lem-plan-review \
    -c 'default_permissions="lem-plan-review"' -a never \
    "$(cat "$REVIEWER_PROMPT")"
  ```

  Costs a file in Codex's settings on each machine, which the ruling "Another program's settings
  stay where that program keeps them" leaves to the owner, and a reply path other than the
  recipe's.
- **Leave it**: the brief's words stay the one guard, at no cost until a reviewer edits.

Both probes checked the file rules, and Sol's checked the mailbox's trusted send rule; neither
started a reviewer in agterm. One real plan talk with the chosen line comes before the harness
file changes: the reply file's write, the live `sent` receipt and the defender's receipt.

Settled by the maintaining session on 2026-11-22 (the owner gave it the design on 2026-11-16): the
first option, the named permission profile on the launch line. It changes no file of the user's,
and the second option needs a file in Codex's own settings, which the ruling "Another program's
settings stay where that program keeps them" leaves to the owner. The task runs one real plan talk
with that line in agterm (a pair of its own, in a throwaway repository) and changes
`second-opinion.md` only when the three receipts above show; when they do not, it leaves the
harness file as it is and rewrites this item with what the talk showed.

Where it surfaced: the outside review of 2026-11-21 (Astra, tip 3, and its answer, point 7; Sol,
finding 9, and its answer, point 5).

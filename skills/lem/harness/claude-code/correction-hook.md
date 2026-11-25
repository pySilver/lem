<!-- lem: old form -->
# Claude Code: the correction hook

A part of `../claude-code.md`, read when the correction queue is offered, turned on or reported.

## The correction hook

For a machine whose owner keeps a correction queue (`stages/learn.md`). The switch is the
machine's: `collect` under `[corrections]` in `~/.config/lem/machine.toml`, which `lem corrections
collect yes` or `lem corrections collect no` writes. It holds in every repository on the machine that
uses Lem, and no file of a repository can hold it: `lem project show` refuses the table in
`.lem/settings.toml` and in `.lem/settings.local.toml`, and names `machine.toml` as its place. The
no is the line `collect = false` there, and a machine with no such line is a no too: the hook exits
at once, and sends nothing. `lem project show` gives the answer as `corrections.collect`, with
`from`, the file or "Lem's default".

The hook comes with the plugin, in its `hooks/hooks.json`, and nobody registers anything. It
starts on each message in every repository where the plugin is on.

A settings file may name the hook too (`~/.claude/settings.json`, or a checkout's
`.claude/settings.local.json`). Beside the plugin it
starts a second copy for each message; the first copy claims the message, so it is still judged
once, and the machine check's `correction hook` row names each such file with the entry to delete
from it by hand. Say that in one line, and do not edit the file: it is the owner's.

- It needs Python 3.14 or newer, as `python3` or as a `python3.N` it finds. Without one it
  judges nothing, and says so in its log. It finds `python3` and `git` on the hook's `PATH`, as any hook does; with no `git`
  there it queues nothing and has nowhere to say so, since git names its state folder. The
  model's client is Lem's own `jev.py`, run through the package's entry by its path. It needs `JEV_API_KEY`, the one name it
  reads for the key, in the environment Claude Code starts with, and `JEV_API_URL` there for a
  provider other than OpenRouter.
- It prints nothing and does not wait for the model: a detached copy asks it. The hook's own two
  waits, for its input and for each of its git calls, end after two seconds each, a bound chosen by guess
  on 2026-11-15. The `timeout` of 10 seconds in `hooks/hooks.json` is the value its source ran with in one
  repository since 2026-11-07; it is not a measurement.
- What fails goes to `corrections.log` in Lem's state folder (`.lem/state/`), and
  `lem corrections list` counts it.
- The yes is a line of a file in the owner's home, which no branch and no review carries. A hook
  that sends the owner's messages to an outside service is his to turn on: the command runs only
  on his answer, in his words. With a `machine.toml` that does not read, the hook sends nothing and
  prints nothing, and `lem project show` refuses with the file's name.

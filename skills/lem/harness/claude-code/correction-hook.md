# Claude Code: the correction hook

A part of `../claude-code.md`, read when the correction queue is offered, turned on or reported.

## The correction hook

For a project that keeps a correction queue (`stages/learn.md`). The hook exits at once in every
repository whose settings do not say `corrections.collect = true`. That line is in the tracked
settings file, so it is the repository's yes: it holds for everybody who works there with the
hook and a key of the Jev model, and everybody can read it in git. Say that to the owner before he
says yes, in those words. One person says no for themselves with `collect = false` under
`[corrections]` in `.lem/project.local.toml`; that file can never say yes.

The hook comes with the plugin, in its `hooks/hooks.json`, and nobody registers anything. It
starts on each message in every repository where the plugin is on.

A settings file may name the hook too (`~/.claude/settings.json`, or a checkout's
`.claude/settings.local.json`). Beside the plugin it
starts a second copy for each message; the first copy claims the message, so it is still judged
once, and the machine check's `correction hook` row names each such file with the entry to delete
from it by hand. Say that in one line, and do not edit the file: it is the owner's.

- It needs Python 3.11 or newer as `python3`. Under an older one it judges nothing, and says so
  in its log. It finds `python3` and `git` on the hook's `PATH`, as any hook does; with no `git`
  there it queues nothing and has nowhere to say so, since git names its state folder. The
  model's client is Lem's own `jev.py`, run by its path. It needs `JEV_API_KEY` in the
  environment Claude Code starts with (`OPENROUTER_API_KEY` of a machine set up before is read
  when it is not set), and `JEV_API_URL` there for a provider other than OpenRouter.
- It prints nothing and does not wait for the model: a detached copy asks it. The hook's own two
  waits, for its input and for each of its git calls, end after two seconds each, a bound chosen by guess
  on 2026-11-15. The `timeout` of 10 seconds in `hooks/hooks.json` is the value its source ran with in one
  repository since 2026-11-07; it is not a measurement.
- What fails goes to `corrections.log` in Lem's state folder (`.lem/state/`), and
  `lem corrections list` counts it.
- The yes is a line of the tracked settings, which a task's branch and the owner's review carry
  like any other change. A hook that sends the owner's messages to an outside service is his to
  turn on: the line goes in only on his yes, in his words.

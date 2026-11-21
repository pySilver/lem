---
worth: later
where: skills/lem/stages/learn.md
added: 2026-11-21
---
# A project's rulings are still one file for each ruling

Lem's own repository keeps the owner's rulings as one list, `docs/rulings/rulings.md`, with
`docs/rulings/history.md` for what a test or one place now holds. In every other project Lem still
writes one file for each ruling into the folder `paths.rulings` names:

- the retro proposes a ruling and writes it as its own file, named by `lem project ruling-file SLUG`
  (`stages/learn.md`, `ruling-file` and `paths.ruling_file` in `skills/lem/scripts/project.py`);
- the question gate's judge reads each file of that folder as one ruling (`skills/lem-gate/`);
- `tests/lem-settings.sh` checks `ruling-file` and the folder as settings.

The owner chose the list for Lem's own rulings on 2026-11-21, after he said three times that the
number of files confused him: "It feel like rulings should be a single file with bullet list, where
each item eventually allows minimal description. This way it will not drift". He said it of Lem's
own folder. Whether it holds for a project's rulings too is a change of the product, and nobody
decided it.

The options:

1. **Leave the product as it is.** A project keeps one file for each ruling. It costs nothing now;
   a project with many rulings gets the folder that confused him here.
2. **A project's rulings become one list too.** `paths.rulings` names a file in place of a folder,
   `ruling_file` goes, the retro adds a bullet under a group, and the gate's judge reads the bullets.
   It changes the settings (a key leaves, one changes its meaning), `stages/learn.md`, the gate's
   judge, `docs/settings.md` and their tests, and each repository that uses Lem is corrected by hand
   ("Lem is not released"). An unmeasured estimate: one task on the standard track.
3. **Both forms.** The settings say which. It keeps two ways of doing one thing, which "Opinionated
   and small" (`docs/rulings/rulings.md`) argues against.

What would settle it: his word on whether "a single file with bullet list" is how he wants the
rulings of every project, or only of Lem's own; and, before option 2, a look at how many rulings a
real project's folder holds after some weeks of retros.

Surfaced in the maintainer's session of 2026-11-21 that made Lem's own list.

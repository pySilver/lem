---
worth: yes
where: src/lem/land.py:cmd_base
added: 2026-11-24
---
# lem land base records a conflict's file names as git quotes them

`cmd_base` reads the names of a stopped rebase with a text-mode `git diff --name-only
--diff-filter=U`. Run at c674b18d in a throwaway repository, git 2.55.0, default settings: a stop on
`café.txt` records `"caf\303\251.txt"`, quotes included, in the conflict and later in the
resolution's `files`, beside `café.txt` from `rebased_files`, which reads `-z` as bytes (5aee49c2).
With `core.quotePath=false`, an unmerged `caf\xe9.txt` raises `UnicodeDecodeError` (APFS refuses
such a name, so on a Mac only the quoted one happens). The names should be read as `rebased_files`
reads them.

Seen on 2026-11-24 beside 5aee49c2, which left this read as it was.

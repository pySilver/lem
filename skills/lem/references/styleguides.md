# Published style guides onboarding offers

A project's style guide is not written from nothing when a well-used public one fits its stack.
Onboarding offers the guides below for the stack it found, and the owner picks one or none.

**A published guide enters a project as a linter configuration and one page of differences, never
as a copy of its text.** The configuration goes into the gate, so a builder meets a rule as a
failed check with the rule's name. The project's style guide file says which guide the project
follows, links it, and lists only where the project differs and the rules of its own that no
linter knows. A copied guide is thousands of lines no one keeps true.

Every repository below existed and was read on 2026-11-14. Check a guide's current state before
adopting it.

| Stack | Guide | Enforced by | Pick it when |
| --- | --- | --- | --- |
| Python | [wemake-python-styleguide](https://github.com/wemake-services/wemake-python-styleguide) | itself: a flake8 plugin | the project wants the strictest set and accepts reading its violations as lessons |
| Python | [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) | pylint with Google's rc file; most of it through [ruff](https://github.com/astral-sh/ruff) rule sets | a team wants a prose guide to point at, with moderate strictness |
| Python | PEP 8 through [ruff](https://github.com/astral-sh/ruff) | ruff, formatter and linter | the default when nothing stricter is wanted |
| Django | [pySilver/django-styleguide](https://github.com/pySilver/django-styleguide) | review lenses and tests; no linter covers it | a service-layer Django project with Pydantic schemas and database triggers on PostgreSQL. It has two complete guides, and a project takes the one that fits: `ASYNC.md` for an async project with TaskIQ, `SYNC.md` for a sync project with Celery. Its last change was 2026-11-15 |
| Django | [HackSoftware/Django-Styleguide](https://github.com/HackSoftware/Django-Styleguide) | review; no linter covers it | a service-and-selector Django project on Django REST Framework |
| JavaScript | [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) | its ESLint configuration | the most used prose guide; a React project |
| JavaScript | [JavaScript Standard Style](https://github.com/standard/standard) | itself, with no configuration | the project wants no decisions at all |
| TypeScript | [Google TypeScript Style](https://github.com/google/gts) | `gts`: formatter and linter in one | a TypeScript project with no existing lint setup |
| Go | [Uber Go Style Guide](https://github.com/uber-go/guide) | [golangci-lint](https://github.com/golangci/golangci-lint) for the part a linter can check | any Go service; read beside Effective Go |
| Swift | [Airbnb Swift Style Guide](https://github.com/airbnb/swift) | its SwiftFormat and [SwiftLint](https://github.com/realm/SwiftLint) rules | an app project |
| Rust | the Rust Style Guide | `rustfmt`, with [Clippy](https://github.com/rust-lang/rust-clippy) for correctness lints | every Rust project; there is no real alternative |
| Kotlin | the Kotlin coding conventions | [ktlint](https://github.com/ktlint/ktlint) | every Kotlin project |
| Ruby | [The Ruby Style Guide](https://github.com/rubocop/ruby-style-guide) | RuboCop | every Ruby project |

A stack that is not here gets no offer: onboarding reads the conventions the code already keeps
and writes those. Add a row when a second project on that stack is onboarded, with the date the
guide was read.

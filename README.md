<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/lem-night.svg">
    <img src="assets/lem.svg" alt="Lem's logo: a tall hooded figure with a red eye holds a long line over a field. Four small figures and the word Lem hang from it. A small glow goes from the tall figure's hands down to the four small figures and lights their red eyes." width="720">
  </picture>
</p>

# Lem

Type a request in plain words, and get a pull request whose first line says green or not green.

For a developer who works alone, and for a team on Linear or GitHub Issues.

Lem is a plugin for Claude Code that works closely with the [agterm](https://agterm.com) terminal:
each task gets its own agterm session and its own worktree. Agents plan, build, test and review
the change. A fresh merge agent reviews each pull request. Lem merges a safe green change. You
merge the others. [The merge](https://pysilver.github.io/lem/docs/merge/) tells which change is
safe.

**The documentation is on the site: [pysilver.github.io/lem](https://pysilver.github.io/lem/).**

## Install

Install the app one time on your computer, then the plugin at the root of your repository:

```bash
brew install pySilver/tap/lem
claude plugin marketplace add pySilver/lem --scope project
claude plugin install lem@lem --scope project
```

Then start Claude Code in agterm there, and type `/lem init`. Lem needs agterm and the tools of
[Install](https://pysilver.github.io/lem/docs/install/), and your repository must be on GitHub.

## Guides

- [How a task goes](https://pysilver.github.io/lem/docs/flow/)
- [When Lem needs you](https://pysilver.github.io/lem/docs/when-lem-needs-you/)
- [The pull request](https://pysilver.github.io/lem/docs/pull-request/)
- [The board](https://pysilver.github.io/lem/docs/board/)
- [Settings](https://pysilver.github.io/lem/docs/settings/)

The source of each page is a file of [`docs/`](docs/).

## Develop Lem

[AGENTS.md](AGENTS.md) gives the rules and the steps for a person who changes Lem itself.

## License

Lem has the [MIT License](LICENSE).

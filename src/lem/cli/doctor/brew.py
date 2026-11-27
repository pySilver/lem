"""The lines of `lem doctor` that install the absent programs through Homebrew: one for the
formulas and one for the casks, since `brew install` takes a cask only with `--cask`."""

FORMULAS = "brew install"
CASKS = "brew install --cask"


def lines(formulas: list[str], casks: list[str]) -> tuple[str, ...]:
    """The line of the formulas and the line of the casks, each only when it names one."""
    said = []
    if formulas:
        said.append(" ".join((FORMULAS, *formulas)))
    if casks:
        said.append(" ".join((CASKS, *casks)))
    return tuple(said)

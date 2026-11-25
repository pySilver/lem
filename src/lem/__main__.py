"""The command `lem`: the command tree, on the arguments it was given."""

import sys

from lem.cli import lazy


def main() -> None:
    """Run the command the arguments name, and exit with its code."""
    sys.exit(lazy.main(sys.argv[1:]))


if __name__ == "__main__":
    main()

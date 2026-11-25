"""`lem help [NOUN]`: the help of `lem`, or of one noun, as `lem NOUN --help` gives it."""

import click


def shown(noun: str | None) -> None:
    """Print the help text, and end the call with no envelope."""
    ctx = click.get_current_context()
    top = ctx.find_root()
    group = top.command
    command = group if noun is None else lookup(group, top, noun)
    if command is None:
        raise click.UsageError(
            f"`lem` has no command {noun}: `lem help` lists them", ctx
        )
    with click.Context(command, info_name=noun, parent=top) as asked:
        click.echo(command.get_help(asked if noun else top))
    raise click.exceptions.Exit(0)


def lookup(group: click.Command, ctx: click.Context, noun: str) -> click.Command | None:
    """The command `noun` names in `group`."""
    if isinstance(group, click.Group):
        return group.get_command(ctx, noun)
    return None


COMMAND = click.Command(
    "help",
    params=[click.Argument(["noun"], required=False)],
    callback=shown,
    help="This text, or the help of one noun: lem help NOUN.",
)

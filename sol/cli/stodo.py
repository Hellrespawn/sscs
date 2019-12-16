# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
import logging
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import click

import sol

from ..tasklist import TaskList

LOG = logging.getLogger(__name__)

ALIASES = {"do": "done", "print": "list", "order": "sort"}

PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")

TODO_NAMES = ("todo", "to-do")  # sscs: skip
DONE_NAMES = ("done", "finished")


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        cmd = click.Group.get_command(self, ctx, cmd_name)
        if cmd is None:
            try:
                cmd = self.get_command(ctx, ALIASES[cmd_name])
            except KeyError:
                pass

        return cmd


def read_tasklist():
    locations = [
        path / (name + ".txt")
        for path in PATHS
        for name in TODO_NAMES  # sscs: skip
    ]
    for location in locations:
        try:
            return TaskList.from_file(location)
        except FileNotFoundError:
            pass

    raise ValueError("Can't read todo.")


@click.command(cls=AliasedGroup, invoke_without_command=True)  # type: ignore
@click.option("-s", "--sort/--no-sort", default=False)
@click.option("-h", "--hide-tags/--show-tags", default=False)
@click.option("-v", "--verbose", count=True, help="level of verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    verbose = kwargs.get("verbose", 0)
    sol.configure_logger(verbose)

    LOG.debug("Args passed to cli(): %s", kwargs)

    ctx.obj = SimpleNamespace(
        **kwargs, tasklist=read_tasklist(), modified=False
    )

    if ctx.invoked_subcommand is None:
        ctx.invoke(end, **kwargs)


@cli.resultcallback()  # type: ignore
@click.pass_context
def end(ctx, *args, **kwargs):
    LOG.debug("Entering callback")
    tasklist = ctx.obj.tasklist
    hide_tags = kwargs.get("hide_tags", False)

    if ctx.obj.modified:
        tasklist.to_file()

    sort = kwargs.get("sort", False)
    if sort:
        tasklist = tasklist.order()

    print(tasklist.to_string(print_index=True, hide_tags=hide_tags))


@cli.command()  # type: ignore
@click.pass_obj
def add(nspace, **kwargs):
    LOG.debug("Entering add")


@cli.command()  # type: ignore
@click.argument("index")
@click.pass_obj
def done(nspace, **kwargs):
    LOG.debug("Entering done")
    index = int(kwargs.get("index", 100000))
    tasklist = nspace.tasklist.order() if nspace.sort else nspace.tasklist

    if index <= 0 or index > len(tasklist):
        raise click.ClickException("Invalid index!")

    tsk = tasklist[index - 1]
    tsk.complete = "" if tsk.complete else "x"
    nspace.modified = True


@cli.command()  # type: ignore
@click.pass_obj
def filter(nspace, **kwargs):
    LOG.debug("Entering filter")


@cli.command(name="sort")  # type: ignore
@click.pass_obj
def sort_(nspace, **kwargs):
    nspace.tasklist = nspace.tasklist.order()
    nspace.modified = True
    LOG.debug("Entering filter")


def main():
    cli()  # pylint: disable=no-value-for-parameter

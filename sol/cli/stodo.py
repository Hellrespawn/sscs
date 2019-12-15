import logging
from pathlib import Path
from datetime import datetime

import click
from click_default_group import DefaultGroup

import sol

from ..tasklist import TaskList

LOG = logging.getLogger(__name__)

ALIASES = {"do": "done", "print": "list"}

PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")

TODO_NAMES = ("todo", "to-do")  # sscs: skip
DONE_NAMES = ("done", "finished")


class AliasedGroup(DefaultGroup):
    def get_command(self, ctx, cmd_name):
        output = click.Group.get_command(self, ctx, cmd_name)
        if output is not None:
            return output

        try:
            return self.get_command(ctx, ALIASES[cmd_name])
        except KeyError:
            super().get_command(ctx, cmd_name)


def read_tasklist():
    locations = [
        path / (name + ".txt") for path in PATHS for name in TODO_NAMES  # sscs: skip
    ]
    for location in locations:
        try:
            with open(location, "r") as file:
                return TaskList.from_iterable(file)
            break
        except FileNotFoundError:
            pass

    else:
        raise ValueError("Can't read todo.")


@click.command(cls=AliasedGroup, default="list", default_if_no_args=True)
@click.option("-v", "--verbose", count=True, help="level of verbosity")
@click.pass_context
def cli(ctx, verbose):
    sol.configure_logger(verbose)
    ctx.obj = read_tasklist()


@cli.resultcallback()
@click.pass_obj
def callback(tasklist, _, **kwargs):
    print("done")


@cli.command()
@click.pass_obj
def add(tasklist):
    print("add")


@cli.command()
@click.pass_obj
def done(tasklist):
    print("done")


@cli.command(name="list")
@click.option("-s", "--sort/--no-sort", default=False)
@click.pass_obj
def list_(tasklist, sort):
    if sort:
        print(tasklist.sort())
    else:
        print(tasklist.string_with_index())


def main():
    sol.configure_logger(999)
    tl = read_tasklist()

    for t in tl:
        print(repr(t))

    print()

    print(tl)
    print()
    tl.sort()
    print(tl)
    print()
    exit()
    cli()

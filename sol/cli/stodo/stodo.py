# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
import argparse
import logging
from pathlib import Path
from typing import Dict
from collections import namedtuple

import sol

from ...tasklist import TaskList
from ..subparser import AccumulatingSubparserAction

LOG = logging.getLogger(__name__)


COMMAND_REGISTER = []

Command = namedtuple("Command", ["name", "type", "aliases"])


def register_command(type_, aliases):
    def wrapper(method):
        command = Command(
            name=method.__name__, type=type_, aliases=list(aliases)
        )
        COMMAND_REGISTER.append(command)
        return method

    return wrapper


class STodo:
    COMMAND_MAP: Dict[str, str] = {}

    DEFAULT_PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")
    DEFAULT_NAMES = ("todo", "to-do", "todo-test")

    def __init__(self, filename=None):
        self.tasklist = None
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        sol.configure_logger(self.args.verbosity)

        self.modified = False

        locations = [
            # path / (name + ".todo.txt")
            path / (name + ".txt")
            for path in self.DEFAULT_PATHS
            for name in self.DEFAULT_NAMES
        ]

        if filename:
            locations = [Path(filename)] + locations

        for location in locations:
            try:
                self.tasklist = TaskList.from_file(location)
                break
            except FileNotFoundError:
                pass
        else:
            raise FileNotFoundError()

    @staticmethod
    def populate_parser(parser, type_):
        if type_ is None:
            return parser

        if type_ == "index":
            parser.add_argument("selection", nargs=1, type=int)

        elif type_ == "sort":
            parser.add_argument(
                "--format",
                "-f",
                choices=["sscs"],
                help="sort according to format",
            )

        return parser

    @classmethod
    def create_subparsers(cls, subparsers, parents=None):
        parents = parents or []

        parsers = []

        for command in COMMAND_REGISTER:
            parser = subparsers.add_parser(
                command.name, aliases=command.aliases, parents=parents
            )
            for alias in [command.name] + command.aliases:
                if alias in cls.COMMAND_MAP:
                    raise ValueError(
                        f"{alias} is already registered to "
                        f"{cls.COMMAND_MAP[alias]}!"
                    )
                cls.COMMAND_MAP[alias] = command.name

            parser = cls.populate_parser(parser, command.type)
            parsers.append(parser)

        return parsers

    @classmethod
    def create_common_parser(cls):
        common_parser = argparse.ArgumentParser(add_help=False)
        common_parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        common_parser.add_argument(
            "--hide-tags",
            "-ht",
            action="store_true",
            help="hide keyword tags",
        )

        return common_parser

    @classmethod
    def create_parser(cls):
        common_parser = cls.create_common_parser()

        root_parser = argparse.ArgumentParser(parents=[common_parser])
        subparsers = root_parser.add_subparsers(
            dest="subcommand", action=AccumulatingSubparserAction
        )

        cls.create_subparsers(subparsers, [common_parser])

        return root_parser

    def get_index(self):
        index = self.args.selection[0] - 1

        if not 0 <= index < len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 < i <= {len(self.tasklist)}"
            )

        return index

    def run_command(self, name):
        try:
            return getattr(self, self.COMMAND_MAP[name])()
        except KeyError:
            if name:
                self.parser.error(f'Unknown command: "{name}"')

    @register_command("index", ["check", "do", "tick"])
    def done(self):
        index = self.get_index()

        self.tasklist[index].complete = (
            "" if self.tasklist[index].complete else "x"
        )

        self.modified = True

    @register_command("sort", ["order"])
    def sort(self):
        # Custom ordering (by project, by context, by keyword)
        format_ = self.args.format

        # Pre-sort
        self.tasklist = self.tasklist.order()
        # Post-sort

        if format_ == "sscs":
            headers = [
                task
                for task in self.tasklist
                if task.keywords.get("c", "") == "header"
            ]
            footers = [
                task
                for task in self.tasklist
                if task.keywords.get("c", "") == "footer"
            ]

            for task in headers + footers:
                self.tasklist.remove(task)

            self.tasklist = TaskList(
                headers + self.tasklist + footers,
                filename=self.tasklist.filename,
            )

        self.modified = True

    @register_command("index", ["delete"])
    def remove(self):
        index = self.get_index()

        # TODO Prompt for removal
        # TODO? Keep history?
        _ = self.tasklist.pop(index)

        self.modified = True

    def main(self):
        print(self.args)
        self.run_command(self.args.subcommand)

        print(self.tasklist.to_string(True, self.args.hide_tags))

        if self.modified:
            self.tasklist.to_file()


def main():
    STodo().main()

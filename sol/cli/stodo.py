# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
import argparse
import logging
from pathlib import Path
from typing import Dict

import sol

from ..tasklist import TaskList
from .subparser import AccumulatingSubparserAction

LOG = logging.getLogger(__name__)


class STodo:
    CMD_TABLE: Dict[str, str] = {}
    DEFAULT_PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")
    DEFAULT_NAMES = ("todo", "to-do", "todo-test")

    def __init__(self, filename=None):
        self.tasklist = None
        self.parser, self.args = self.create_parser()
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
        if type_ == "index":
            parser.add_argument("selection", nargs=1, type=int)

        return parser

    @classmethod
    def create_subparser(cls, subparsers, name, aliases, type_, parents=None):
        parents = parents or []

        for alias in aliases:
            if alias in cls.CMD_TABLE:
                raise ValueError(
                    f'"{alias}" is already an alias '
                    f'for "{cls.CMD_TABLE[alias]}"'
                )
            cls.CMD_TABLE[alias] = name
        cls.CMD_TABLE[name] = name

        parser = subparsers.add_parser(name, aliases=aliases, parents=parents)
        parser = cls.populate_parser(parser, type_)

        return parser

    @classmethod
    def create_common_parser(cls):
        common_parser = argparse.ArgumentParser(add_help=False)
        common_parser.add_argument(
            "--verbose",
            "-v",
            # action=cls.GlobalCounter,
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )
        common_parser.add_argument(
            "--sort", "-s", action="store_true", help="sort displayed list",
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

        cls.create_subparser(
            subparsers,
            "done",
            ["do", "check", "tick"],
            "index",
            [common_parser],
        )

        sort_parser = cls.create_subparser(
            subparsers, "sort", ["order"], None, [common_parser],
        )

        sort_parser.add_argument(
            "--format",
            "-f",
            choices=["sscs"],
            help="sort according to format",
        )

        args = root_parser.parse_args()

        return root_parser, args

    def run_command(self, name):
        try:
            return getattr(self, self.CMD_TABLE[name])()
        except KeyError:
            if name:
                self.parser.error(f'Unknown command: "{name}"')

    def done(self):
        index = self.args.selection[0] - 1

        if not 0 <= index < len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 < i <= {len(self.tasklist)}"
            )

        if self.args.sort:
            self.tasklist = self.tasklist.order()

        self.tasklist[index].complete = (
            "" if self.tasklist[index].complete else "x"
        )

        self.modified = True

    def sort(self):
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

    def main(self):
        print(self.args)
        self.run_command(self.args.subcommand)

        if self.args.sort:
            print(self.tasklist.order().to_string(True))
        else:
            print(self.tasklist.to_string(True))

        if self.modified:
            self.tasklist.to_file()


def main():
    STodo().main()

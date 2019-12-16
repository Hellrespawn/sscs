# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
import argparse
import logging
from pathlib import Path
from typing import Callable, Dict

import sol

from ..tasklist import TaskList

LOG = logging.getLogger(__name__)

CMD_TABLE: Dict[str, Callable] = {"": lambda *x: None}


def command(*aliases):
    def wrapper(method):
        for alias in (method.__name__, *aliases):
            if alias in CMD_TABLE:
                raise ValueError(
                    f'"{alias}" is already an alias for "{CMD_TABLE[alias]}"'
                )
            CMD_TABLE[alias] = method
        return method

    return wrapper


class STodo:
    DEFAULT_PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")
    DEFAULT_NAMES = ("todo", "to-do", "todo-test")

    def __init__(self, filename=None):
        self.tasklist = None
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

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
    def create_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        parser.add_argument("--format", "-f", help="format for sort")
        parser.add_argument(
            "--sort", "-s", action="store_true", help="sort displayed list"
        )
        parser.add_argument(
            "--hide-tags",
            "-ht",
            action="store_true",
            help="hide keyword tags",
        )

        parser.add_argument("command", nargs="?", default="")
        parser.add_argument("arguments", nargs="*")

        return parser

    def run_command(self, name):
        try:
            return CMD_TABLE[name](self)
        except KeyError:
            self.parser.error(f'Unknown command: "{name}"')

    def validate_args(self, num, type_):
        args = self.args.arguments

        if len(args) != num:
            self.parser.error(f"{num} argument(s) expected, got {len(args)}!")

        try:
            args = [type_(arg) for arg in args]
        except ValueError:
            self.parser.error(f"Unable to parse arguments as {type_}!")

        if num == 1:
            return args[0]

        return args

    @command("check", "do", "tick")
    def done(self):
        index = self.validate_args(1, int) - 1

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

    @command("order")
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
        self.run_command(self.args.command)

        if self.args.sort:
            print(self.tasklist.order().to_string(True))
        else:
            print(self.tasklist.to_string(True))

        if self.modified:
            self.tasklist.to_file()


def main():
    STodo().main()

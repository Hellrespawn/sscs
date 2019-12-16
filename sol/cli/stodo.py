# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
import argparse
import logging
from pathlib import Path
from typing import Dict

import sol

from ..tasklist import TaskList

LOG = logging.getLogger(__name__)

CMD_TABLE: Dict[str, str] = {}


def alias(*names):
    def wrapper(method):
        for name in [method.__name__, *names]:
            if name in CMD_TABLE:
                raise ValueError(
                    f'"{name}" is already an alias for "{CMD_TABLE[name]}"'
                )
            CMD_TABLE[name] = method.__name__
        return method

    return wrapper


class STodo:
    DEFAULT_PATHS = (Path.home(), sol.LOG_FOLDER.parent / "doc")
    DEFAULT_NAMES = ("todo", "to-do")

    def __init__(self, filename=None):
        self.tasklist = None
        self.parser = argparse.ArgumentParser()
        self.args = None

        locations = [
            # path / (name + ".todo.txt")
            path / (name + ".txt")
            for path in self.DEFAULT_PATHS
            for name in self.DEFAULT_NAMES
        ]

        if filename:
            locations = [Path(filename)] + locations

        print(locations)

        for location in locations:
            try:
                self.tasklist = TaskList.from_file(location)
                break
            except FileNotFoundError:
                pass
        else:
            raise FileNotFoundError()

    def parse_args(self) -> argparse.Namespace:
        self.parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        self.parser.add_argument("--sort", "-s", help="Display sorted list")
        self.parser.add_argument("--hide-tags", "-ht", help="Hide keyword tags")

        self.parser.add_argument("command", nargs="?", default="print")
        self.parser.add_argument("argument", nargs="*")

        self.args = self.parser.parse_args()

        return self.args

    @alias("list", "l", "p")
    def print(self):
        print(self.tasklist.to_string(True))

    def get_method(self, name):
        try:
            return getattr(self, CMD_TABLE[name])
        except KeyError:
            self.parser.error(f'Unknown function: "{name}"')

    def main(self):
        args = self.parse_args()
        print(args)
        print(CMD_TABLE)
        self.get_method(args.command)()


def main():
    STodo().main()

# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO Settings support
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import sol

from ..tasklist import SSCS, TaskList
from .cliapp import Argument, CLIApp, register_command

LOG = logging.getLogger(__name__)


class STodo(CLIApp):
    DEFAULT_PATHS: List[Path] = [Path.home(), sol.LOG_FOLDER.parent / "doc"]
    DEFAULT_NAMES: List[str] = ["todo", "to-do", "todo-test"]

    MODES: List[str] = ["todotxt", "sscs"]

    def __init__(self, filename: Path = None) -> None:
        super().__init__(self.common_options())
        sol.configure_logger(self.settings.verbosity)

        locations: List[Path] = [
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
                self.filename = location
                break
            except FileNotFoundError:
                pass
        else:
            # TODO? Create new file here?
            raise FileNotFoundError("Unable to find valid file!")

        if self.settings.mode == "sscs":
            self.tasklist = SSCS(self.tasklist)

        self.modified = False

    @classmethod
    def common_options(cls):
        common_options = argparse.ArgumentParser(add_help=False)

        common_options.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        common_options.add_argument(
            "--skip-tags", "-st", action="store_true",
        )

        common_options.add_argument(
            "--mode", "-m", choices=cls.MODES, default="todotxt",
        )

        return common_options

    def update_footer(self):
        if self.tasklist.footers:
            for task in self.tasklist.footers:
                msg = " ".join(task.msg.split()[-2:])
                try:
                    datetime.strptime(msg, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    continue

                task.msg = datetime.now().strftime(
                    "c:footer Generated on %Y-%m-%d %H:%M:%S.%f"
                )
                break

    def get_index(self) -> int:
        index = int(self.settings.index[0])

        if not 1 <= index <= len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 <= i <= {len(self.tasklist)}"
            )

        return index

    #
    # Commands
    #
    @register_command(
        "check", "do", "tick", "index", kwargs=[Argument("index")]
    )
    def done(self) -> None:
        index = self.get_index()

        self.tasklist[index].complete = (
            "" if self.tasklist[index].complete else "x"
        )

        self.modified = True

    # @register_command("order")
    # def sort(self) -> None:
    #     pass

    # @register_command("delete", kwargs=[Argument("index")])
    # def remove(self) -> None:
    #     pass

    @register_command()
    def print(self) -> None:
        print(self.tasklist.to_string(True, self.settings.skip_tags))

    def post_command(self):
        self.print()

        if self.settings.mode == "sscs":
            self.update_footer()

        if self.modified:
            self.tasklist.to_file()


def main():
    from cliapp import TestApp
    sol.configure_logger(4)
    TestApp().main()

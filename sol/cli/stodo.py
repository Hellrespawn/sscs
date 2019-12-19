# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO Settings support
# TODO Colorize output
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import sol

from ..task import Task
from ..tasklist import SSCS, TaskList
from .cliapp import CLIApp, Register

LOG = logging.getLogger(__name__)


class STodo(CLIApp):
    DEFAULT_NAMES: List[str] = ["todo", "to-do", "todo-test"]

    MODES: List[str] = ["todotxt", "sscs"]

    def __init__(self, filename: Path = None) -> None:
        super().__init__(self.common_options())

        sol.configure_logger(self.settings.verbosity)

        try:
            location = Path.expanduser(Path(self.settings.todofile))
            self.tasklist = TaskList.from_file(location)
            self.filename = location
        except (FileNotFoundError, AttributeError):
            locations = [
                self.config_dir / (name + ".txt")
                for name in self.DEFAULT_NAMES
            ]
            for location in locations:
                try:
                    self.tasklist = TaskList.from_file(location)
                    break
                except FileNotFoundError:
                    pass
            else:
                raise FileNotFoundError(
                    "Can't find text file! Please set todofile in cfg."
                ) from None

        self.settings = self.update_settings()

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

    def update_settings(self):
        for task in self.tasklist:
            if not task.keywords.get("header") == "options":
                continue

            for option in task.keywords:
                if option == "header":
                    continue

                if getattr(self.settings, option):
                    LOG.warning(
                        "Existing option %s is being clobbered by header.",
                        option,
                    )
                setattr(self.settings, option, task.keywords[option])

        LOG.debug(f"Updated settings:\n{self.settings}")
        return self.settings

    def update_footer(self):
        # TODO? Use dateutil to parse times dynamically
        time_fmt = "%Y-%m-%d %H:%M:%S.%f"
        fmt_length = len(time_fmt.split())

        if self.tasklist.footers:
            for task in self.tasklist.footers:
                if task.keywords.get("footer") != "time":
                    continue

                parts = task.msg.split()

                date = " ".join(parts[-fmt_length:])
                msg = " ".join(parts[:-fmt_length])

                try:
                    datetime.strptime(date, time_fmt)
                except ValueError:
                    continue

                task.msg = " ".join((msg, datetime.now().strftime(time_fmt)))
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
    @Register.command("check", "do", "tick", "index")
    @Register.argument("index")
    def done(self) -> None:
        index = self.get_index()
        task = self.tasklist.get(index)

        task.complete = "" if task.complete else "x"

        self.modified = True

    @Register.command()
    @Register.argument("task")
    @Register.argument("--date", "-d", action="store_true")
    def add(self):
        task = Task.from_string(self.settings.task)
        if self.settings.date:
            task.date_created = datetime.now()
        print(task)
        print(repr(task))

    # @register_command("order")
    # def sort(self) -> None:
    #     pass

    # @register_command("delete", kwargs=[Argument("index")])
    # def remove(self) -> None:
    #     pass

    @Register.command()
    def print(self) -> None:
        print(self.tasklist.to_string(True, self.settings.skip_tags))

    def post_command(self):
        self.print()

        if self.settings.mode == "sscs":
            self.update_footer()

        if self.modified:
            self.tasklist.to_file()


def main():
    sol.configure_logger(4)
    STodo().main()

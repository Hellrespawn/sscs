# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO Settings support
# TODO Colorize output
# TODO? Do validation on options?
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from types import SimpleNamespace

import cliapp
import sol
from cliapp.cliapp import CLIApp
from cliapp.register import Register

from ..task import Task
from ..tasklist import SolTaskList, TaskList

# from sol import EXTRA_VERBOSE


LOG = logging.getLogger(__name__)


class STodo(CLIApp):
    MODES: List[str] = ["todotxt", "sol"]

    def __init__(self, filename: Path = None) -> None:
        filename, remaining_args = self.handle_early_args()

        super().__init__()

        self.settings: SimpleNamespace

        try:
            if filename is not None:
                self.filename = Path(filename)
                if not self.filename.exists():
                    self.parser.error(
                        f'Unable to open "{Path(filename)}"!'
                    )
            else:
                self.filename = Path(self.settings.todofile)

            self.tasklist = TaskList.from_file(Path.expanduser(self.filename))

        except (AttributeError, FileNotFoundError):
            files = [
                path
                for path in self.config_dir.iterdir()
                if path.is_file()
            ]
            for file in files:
                if str(file).endswith(".todo.txt"):
                    try:
                        self.tasklist = TaskList.from_file(file)
                        self.filename = file
                        break
                    except FileNotFoundError:
                        pass

            else:
                raise FileNotFoundError(
                    "Can't find text file! Please set todofile in cfg."
                ) from None

        self.settings = self.read_settings_from_tasklist()
        self.settings = self.read_settings_from_args(
            self.parse_args(args_in=remaining_args)
        )
        LOG.debug("Final settings:\n%s", self.settings)

        if self.settings.mode == "sol":
            self.tasklist = SolTaskList(self.tasklist)

        self.modified: bool = False

    def handle_early_args(self):
        # TODO Catch exception and "play it back" with self.parser
        # TODO? Integrate with common_options?
        # TODO? Add first two options to common_parser, parse_known_args, add
        # TODO? rest of options, pass on to cliapp
        early_parser = argparse.ArgumentParser()
        early_parser.add_argument("--todo-file", "-t")
        early_parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        args, remaining_args = early_parser.parse_known_args()

        sol.configure_logger(args.verbosity)
        cliapp.configure_logger(args.verbosity, sol.LOG_FOLDER)

        return args.todo_file, remaining_args

    @classmethod
    def get_common_options(cls):
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
            "--mode", "-m", choices=cls.MODES, default=argparse.SUPPRESS
        )

        return common_options

    def read_settings_from_tasklist(self):
        for task in self.tasklist:
            if not task.keywords.get("header") == "options":
                continue

            for option in task.keywords:
                if option == "header":
                    continue

                setattr(self.settings, option, task.keywords[option])

        LOG.debug(f"Settings after taskfile:\n{self.settings}")
        return self.settings

    def read_settings_from_args(self, args: argparse.Namespace):
        for option, value in vars(args).items():
            # current_option = getattr(self.settings, option, None)
            setattr(self.settings, option, value)

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
        print(f"{self.filename}:")
        print(self.tasklist.to_string(True, self.settings.skip_tags))

    def post_command(self):
        self.print()

        if self.settings.mode == "sol":
            self.update_footer()

        if self.modified:
            self.tasklist.to_file()


def main():
    STodo().main()

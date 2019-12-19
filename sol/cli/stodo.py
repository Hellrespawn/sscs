# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO Colorize output
# TODO? Do validation on options?
import argparse
import logging
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

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
                    self.parser.error(f'Unable to open "{Path(filename)}"!')
            else:
                self.filename = Path(self.settings.todo_file)

            self.tasklist = TaskList.from_file(Path.expanduser(self.filename))

        except (AttributeError, FileNotFoundError):
            files = [
                path for path in self.config_dir.iterdir() if path.is_file()
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
                    "Can't find text file! Please set todo-file in cfg."
                ) from None

        self.settings = self.read_settings_from_tasklist()
        self.settings = self.read_settings_from_args(
            self.parse_args(args_in=remaining_args)
        )
        LOG.debug("Final settings:\n%s", self.settings)

        if self.settings.mode == "sol":
            self.tasklist = SolTaskList(self.tasklist)

        self.modified: bool = False
        self.print_list: Optional[TaskList] = None

    #################################################
    #    Parsing arguments and reading settings     #
    #################################################
    def handle_early_args(self):
        early_parser = self.get_common_options(1)
        args, remaining_args = early_parser.parse_known_args()
        sol.configure_logger(args.verbosity)

        return args.todo_file, remaining_args

    @classmethod
    def get_common_options(cls, stage=2):  # pylint: disable=arguments-differ
        common_options = argparse.ArgumentParser(add_help=False)

        if stage >= 1:
            common_options.add_argument(
                "--verbose",
                "-v",
                action="count",
                default=0,
                dest="verbosity",
                help="increase verbosity",
            )

            common_options.add_argument("--todo-file", "-t")

        if stage >= 2:
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

    ###############################
    #    Support for commands     #
    ###############################
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
        index = int(self.get_setting("index"))

        if not 1 <= index <= len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 <= i <= {len(self.tasklist)}"
            )

        return index

    ###################
    #    Commands     #
    ###################
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
    @Register.argument("--index", "-i", default=None)
    def add(self):
        task = Task.from_string(self.get_setting("task"))
        if self.get_setting("date"):
            task.date_created = datetime.now()
        print(task)
        print(repr(task))

        # TODO? Prompt or require flag before appending?

        if self.get_setting("index") is not None:
            self.tasklist.insert(self.get_index() - 1, task)

        else:
            self.tasklist.append(task)

        self.modified = True

    @Register.command("order")
    def sort(self) -> None:
        self.tasklist.sort()
        self.modified = True

    @Register.command("search")
    @Register.argument("query")
    @Register.argument(
        "--by", '-by',
        choices=["project", "context", "keyword", "message", "msg"],
        dest="target",
        default="message",
    )
    @Register.argument("--strict", action="store_true")
    @Register.argument("--case-sensitive", "-cs", action="store_true")
    def filter(self):
        # TODO Highlight searches
        query = self.get_setting("query")
        target = self.get_setting("target")
        if target == "message":
            target = "msg"
        strict = self.get_setting("strict", bool)
        case_sens = self.get_setting("case_sensitive", bool)

        self.print_list = self.tasklist.filter_by(
            query, target, strict, case_sens
        )

    # @register_command("delete", kwargs=[Argument("index")])
    # def remove(self) -> None:
    #     pass

    @Register.command()
    def print(self) -> None:
        tasklist = self.print_list or self.tasklist
        print(f"{self.filename}:")
        print(tasklist.to_string(True, self.get_setting("skip_tags")))

    def post_command(self):
        self.print()

        if self.settings.mode == "sol":
            self.update_footer()

        if self.get_setting("keep_sorted", bool) and self.tasklist.sort():
            self.modified = True

        if self.modified:
            self.tasklist.to_file()


def main():
    STodo().main()

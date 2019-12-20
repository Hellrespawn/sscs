# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO Colorize output
# TODO? Do validation on options?
# TODO Multiple indices at the same time
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
        self.settings: SimpleNamespace

        filename, remaining_args = self.handle_early_args()

        super().__init__()

        self.tasklist = self.read_tasklist(filename)

        self.settings = self.merge_settings_from_tasklist()
        self.settings = self.merge_settings_from_args(
            self.parse_args(args_in=remaining_args)
        )
        LOG.debug("Final settings:\n%s", self.settings)

        if self.get_setting("mode") == "sol":
            self.tasklist = SolTaskList(self.tasklist)

        self.modified: bool = False
        self.print_list: Optional[TaskList] = self.tasklist

    #################################################
    #    Parsing arguments and reading settings     #
    #################################################

    # Overrides cliapp
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

    def run_command(self, name: str = None):
        if name is None:
            return super().run_command()

        mode = self.get_setting("mode")
        for title in (f"{name}_{mode}", name):
            try:
                return super().run_command(title)
            except ValueError:
                pass

        raise ValueError(f'Unable to run command "{name}"')

    def handle_early_args(self):
        early_parser = self.get_common_options(1)
        args, remaining_args = early_parser.parse_known_args()
        sol.configure_logger(args.verbosity)

        return args.todo_file, remaining_args

    def read_tasklist_from_args(self, filename):
        tasklist = None

        if filename is not None:
            try:
                filename = Path(filename)
                tasklist = TaskList.from_file(filename)
            except FileNotFoundError:
                self.parser.error(f'Unable to open "{Path(filename)}"!')

        return tasklist

    def read_tasklist_from_settings(self, _):
        tasklist = None

        try:
            raw_filename = self.get_setting("todo_file")
            if raw_filename is not None:
                filename = Path(raw_filename)
                tasklist = TaskList.from_file(filename)

        except TypeError:
            self.parser.error(
                f'Unable to open "{filename}." Check your '
                "configuration."
            )

        except AttributeError:
            pass

        return tasklist

    def read_tasklist_from_default_locations(self, _):
        tasklist = None

        files = [
            path for path in self.config_dir.iterdir() if path.is_file()
        ]
        for filename in files:
            if str(filename).endswith(".todo.txt"):
                try:
                    tasklist = TaskList.from_file(filename)
                    break
                except FileNotFoundError:
                    pass

        return tasklist

    def read_tasklist(self, filename):
        read_functions = (
            self.read_tasklist_from_args,
            self.read_tasklist_from_settings,
            self.read_tasklist_from_default_locations
        )

        tasklist = None

        for function in read_functions:
            tasklist = function(filename)
            if tasklist is not None:
                break

        else:
            raise FileNotFoundError("Can't find todo-file anywhere!")

        return tasklist

    def merge_settings_from_tasklist(self):
        for task in self.tasklist:
            if not task.keywords.get("header") == "options":
                continue

            for option in task.keywords:
                if option == "header":
                    continue

                self.set_setting(option, task.keywords[option])

        LOG.debug(f"Settings after taskfile:\n{self.settings}")
        return self.settings

    def merge_settings_from_args(self, args: argparse.Namespace):
        for option, value in vars(args).items():
            # current_option = getattr(self.settings, option, None)
            self.set_setting(option, value)

        return self.settings

    ###############################
    #    Support for commands     #
    ###############################
    def update_footer(self):
        # TODO? Use dateutil to parse times dynamically
        time_fmt = "%Y-%m-%d %H:%M:%S.%f"
        fmt_length = len(time_fmt.split())

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
        else:
            self.tasklist.append(
                Task(
                    "footer:time Generated on "
                    f"{datetime.now().strftime(time_fmt)}"
                )
            )

    def get_index(self) -> int:
        index = int(self.get_setting("index"))

        if not 1 <= index <= len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 <= i <= {len(self.tasklist)}"
            )

        return index

    def get_archive_filename(self):
        archive_file = self.get_setting("archive_file")
        if not archive_file:
            name = str(self.tasklist.filename.name).replace(
                ".txt", ".archive.txt"
            )
            archive_file = self.tasklist.filename.parent / name

        return archive_file

    def prompt(self, query, default=False):
        # TODO Implement prompt()
        print(query)
        return default

    def write_to_file(self):
        self.tasklist.to_file()

    ###################
    #    Commands     #
    ###################
    @Register.command("check", "do", "tick")
    @Register.argument("index")
    def done(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

        if task.complete == "x":
            self.parser.error("Task is already completed!")
        task.complete = "x"

        self.modified = True

    @Register.command("uncheck", "untick")
    @Register.argument("index")
    def undo(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

        if task.complete == "":
            self.parser.error("Task is already not completed!")
        task.complete = ""

        self.modified = True

    @Register.command()
    @Register.argument("index")
    def toggle(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

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

    @Register.command()
    @Register.argument("index")
    def remove(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_pop(index)

        if self.prompt(f'Removing "{task.to_string()}"\nAre you sure?'):
            self.modified = True

        else:
            self.tasklist.insert(index, task)

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

    @Register.command()
    def archive(self):
        archive = self.tasklist.filter_by("x", "complete", strict=True)
        for task in archive:
            self.tasklist.remove(task)
            task.complete = ""

        archive_file = self.get_setting("archive_file")
        if not archive_file:
            name = str(archive.filename.name).replace(".txt", ".archive.txt")
            archive_file = archive.filename.parent / name

        archive.filename = self.get_archive_filename()
        archive.headers = self.tasklist.headers
        archive.footers = self.tasklist.footers
        archive.to_file()

        self.modified = True

    @Register.command()
    @Register.argument("-a", "--archive", action="store_true")
    def print(self) -> None:
        tasklist = self.print_list
        if self.get_setting("archive", bool):
            # TODO Open archive here, check for correct class
            pass

        print(f"{tasklist.filename}:")
        print(tasklist.to_string(True, self.get_setting("skip_tags")))
        self.print_list = None

    def post_command(self):
        if self.print_list:
            self.print()

        if self.get_setting("mode") == "sol":
            self.update_footer()

        if self.get_setting("keep_sorted", bool) and self.tasklist.sort():
            self.modified = True

        if self.modified:
            self.write_to_file()


def main():
    STodo().main()

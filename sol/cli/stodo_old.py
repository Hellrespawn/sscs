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
from loggingextra import configure_logger

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

        if self.settings.get("mode") == "sol":
            self.tasklist = SolTaskList(self.tasklist)

        self.modified_list: bool = False
        self.modified_archive: bool = False
        self.print_list: Optional[TaskList] = self.tasklist

    @property
    def tasklist_archive(self):
        archive_file = self.settings.get("archive_file")
        return archive_file or self._tasklist_archive

    @property
    def tasklist(self):
        return self._tasklist

    @tasklist.setter
    def tasklist(self, value: TaskList):
        self._tasklist = value

        name = str(self.tasklist.filename.name).replace(
            ".txt", ".archive.txt"
        )
        try:
            self._tasklist_archive = type(self._tasklist).from_file(
                filename=self.tasklist.filename.parent / name
            )
        except FileNotFoundError:
            self._tasklist_archive = type(self._tasklist)(
                filename=self.tasklist.filename.parent / name
            )
            if self.settings.get("mode") == "sol":
                self.update_footer(self._tasklist_archive)

    #################################################
    #    Parsing arguments and reading settings     #
    #################################################

    def handle_early_args(self):
        early_parser = self.create_common_parser(1)
        args, remaining_args = early_parser.parse_known_args()
        configure_logger(args.verbosity, sol.LOG_PATH, sol.__name__)

        return args.todo_file, remaining_args

    @classmethod
    def create_common_parser(
        cls, stage=2
    ):  # pylint: disable=arguments-differ
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
                f'Unable to open "{filename}." Check your ' "configuration."
            )

        except AttributeError:
            pass

        return tasklist

    def read_tasklist_from_default_locations(self, _):
        tasklist = None

        files = [path for path in self.config_dir.iterdir() if path.is_file()]
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
            self.read_tasklist_from_default_locations,
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

                self.settings[option] = task.keywords[option]

        LOG.debug(f"Settings after taskfile:\n{self.settings}")
        return self.settings

    def merge_settings_from_args(self, args: argparse.Namespace):
        for option, value in vars(args).items():
            # current_option = getattr(self.settings, option, None)
            self.settings[option] = value

        return self.settings

    def run_command(self, name: str = None):
        if name is None:
            return super().run_command()

        mode = self.settings.get("mode")
        for title in (f"{name}_{mode}", name):
            try:
                return super().run_command(title)
            except ValueError:
                pass

        raise ValueError(f'Unable to run command "{name}"')

    ###############################
    #    Support for commands     #
    ###############################
    @staticmethod
    def update_footer(tasklist):
        # TODO? Use dateutil to parse times dynamically
        time_fmt = "%Y-%m-%d %H:%M:%S.%f"
        msg = f"footer:time Generated on {datetime.now().strftime(time_fmt)}"

        for task in tasklist.footers:
            if task.keywords.get("footer") == "time":
                task.msg = msg
                break

        else:
            tasklist.append(Task(msg))

    def get_index(self) -> int:
        index = int(self.settings.get("index"))

        if not 1 <= index <= len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 <= i <= {len(self.tasklist)}"
            )

        return index

    def prompt(self, query, default=False):
        # TODO Implement prompt()
        print(query)
        return default

    def print_header(self, tasklist):
        strings = (
            f"{tasklist.filename}:",
            "mode: " + self.settings.get("mode"),
        )

        width, _ = self.get_terminal_size()
        for string in strings:
            width -= len(string)

        print((width // (len(strings) - 1) * " ").join(strings))

    def write_to_file(self):
        # TODO? Delete file if empty?
        if self.modified_list:
            self.tasklist.to_file()

        if self.modified_archive:
            self.tasklist_archive.to_file()

    ###################
    #    Commands     #
    ###################
    @Register.command("check", "do", "tick")
    @Register.argument("index")
    def done(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

        if task.complete:
            self.parser.error("Task is already completed!")
        task.complete = True

        self.modified_list = True

    @Register.command("uncheck", "untick")
    @Register.argument("index")
    def undo(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

        if not task.complete:
            self.parser.error("Task is already not completed!")
        task.complete = False

        self.modified_list = True

    @Register.command()
    @Register.argument("index")
    def toggle(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_get(index)

        task.complete = False if task.complete else True

        self.modified_list = True

    @Register.command()
    @Register.argument("task")
    @Register.argument("--date", "-d", action="store_true")
    @Register.argument("--index", "-i", default=None)
    def add(self):
        task = Task.from_string(self.settings.get("task"))
        if self.settings.get("date"):
            task.date_created = datetime.now()
        print(task)
        print(repr(task))

        # TODO? Prompt or require flag before appending?

        if self.settings.get("index") is not None:
            self.tasklist.insert(self.get_index() - 1, task)

        else:
            self.tasklist.append(task)

        self.modified_list = True

    @Register.command()
    @Register.argument("index")
    def remove(self) -> None:
        index = self.get_index()
        task = self.tasklist.safe_pop(index)

        if self.prompt(f'Removing "{task.to_string()}"\nAre you sure?'):
            self.modified_list = True

        else:
            self.tasklist.insert(index, task)

    @Register.command("order")
    def sort(self) -> None:
        self.tasklist.sort()
        self.modified_list = True

    @Register.command("search")
    @Register.argument("query")
    @Register.argument(
        "--by",
        "-by",
        choices=["project", "context", "keyword", "message", "msg"],
        dest="target",
        default="message",
    )
    @Register.argument("--strict", action="store_true")
    @Register.argument("--case-sensitive", "-cs", action="store_true")
    def filter(self):
        # TODO Highlight searches
        query = self.settings.get("query")
        target = self.settings.get("target")
        if target == "message":
            target = "msg"
        strict = self.settings.get("strict")
        case_sens = self.settings.get("case_sensitive")

        self.print_list = self.tasklist.filter_by(
            query, target, strict, case_sens
        )

    @Register.command()
    def archive(self):
        for task in self.tasklist:
            if task.complete:
                self.tasklist.remove(task)
                task.complete = False
                self.tasklist_archive.append(task)

        self.modified_list = True
        self.modified_archive = True

    @Register.command()
    def unarchive(self):
        for task in self.tasklist_archive:
            self.tasklist_archive.remove(task)
            self.tasklist.append(task)

        self.modified_list = True
        self.modified_archive = True

    @Register.command()
    @Register.argument("-a", "--archive", action="store_true")
    def print(self) -> None:
        if self.settings.get("archive"):
            self.print_list = self.tasklist_archive

        if self.print_list:
            self.print_header(self.print_list)
            print(
                self.print_list.to_string(
                    True, self.settings.get("skip_tags")
                )
            )

            # Disable auto-print
            self.print_list = None

    def post_command(self):
        if self.print_list:
            self.print()

        if self.settings.get("mode") == "sol":
            self.update_footer(self.tasklist)

        if self.settings.get("keep_sorted") and self.tasklist.sort():
            self.modified_list = True

        self.write_to_file()


def main():
    STodo().main()

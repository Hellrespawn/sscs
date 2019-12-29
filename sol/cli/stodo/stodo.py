import argparse
import configparser
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sol
from loggingextra import VERBOSE, configure_logger

from ...task import Task
from .helpers import Command, modifies, no_default

LOG = logging.getLogger(__name__)


class STodo:
    DEFAULT_DIR = Path.expanduser(Path("~/.sol"))

    COMMAND_LIST = [
        Command(["default", ""]),
        Command(["do", "done"], dest="do_task"),
        Command(["undo"]),
        Command(["listarchive"]),
    ]

    def __init__(self) -> None:
        self.parser = self.create_parser()
        try:
            self.args = self.parser.parse_args()

            configure_logger(self.args.verbosity, sol.LOG_PATH, sol.__name__)
            LOG.debug(f"Command line args:\n{self.args}")

            self.settings = self.read_settings()
            LOG.debug(f"Settings:\n{self.settings}")

            self.todo, self.done = self.read_lists_from_file()

            self.run_default = True
            self.modified_todo = False
            self.modified_done = False

            self.name = Path(sys.argv[0]).name

        except Exception as exc:
            self.error(exc)

    def error(self, exc):
        if LOG.isEnabledFor(logging.DEBUG):
            raise exc from None

        self.parser.error(exc)

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity.",
        )

        parser.add_argument(
            "--config-file",
            "-c",
            dest="config",
            help=(
                "Use a configuration file other than the "
                f"default {self.DEFAULT_DIR / 'config'}."
            ),
        )

        parser.add_argument(
            "-@",
            action="count",
            default=0,
            dest="hide_contexts",
            help="hide context names in list.",
        )

        parser.add_argument(
            "-+",
            action="count",
            default=0,
            dest="hide_projects",
            help="hide project names in list.",
        )

        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="forces actions without confirmation.",
        )

        # color_mutex = parser.add_mutually_exclusive_group()
        # color_mutex.add_argument(
        #     "--color", "-c", action="store_true", help="enable color mode.",
        # )

        # color_mutex.add_argument(
        #     "--plain", "-p", action="store_true", help="disable color mode.",
        # )

        command_choices = []
        for command in self.COMMAND_LIST:
            if command.name != "default":
                command_choices.extend(command.aliases)

        parser.add_argument(
            "command",
            choices=sorted(command_choices),
            default=None,
            nargs="?",
            help="command to run",
        )

        parser.add_argument(
            "arguments",
            # choices=[],
            nargs=argparse.REMAINDER,
            help="arguments for command",
        )

        return parser

    def read_settings(self) -> Dict[str, Any]:
        cfg = configparser.ConfigParser()

        cfg_file = (
            Path(self.args.config)
            if self.args.config
            else self.DEFAULT_DIR / "config"
        )

        try:
            with open(Path.expanduser(cfg_file)) as file:
                cfg.read_string("\n".join([f"[dummy]"] + file.readlines()))

            settings = self.parse_settings(dict(cfg["dummy"]))

        except FileNotFoundError:
            if self.args.config:
                raise ValueError(
                    f'Unable to read "{self.args.config}" as config!'
                )

            settings = self.parse_settings({})

        return settings

    def parse_settings(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        settings = {}

        todo_dir = Path.expanduser(
            Path(cfg.pop("todo-dir", self.DEFAULT_DIR))
        )
        LOG.log(VERBOSE, "todo_dir: %s", todo_dir)

        settings["todo-file"] = Path.expanduser(
            Path(cfg.pop("todo-file", "todo.txt"))
        )
        LOG.log(VERBOSE, "todo_file: %s", settings["todo-file"])

        if not settings["todo-file"].is_absolute():
            settings["todo-file"] = todo_dir / settings["todo-file"]
            LOG.log(VERBOSE, "absolute todo_file: %s", settings["todo-file"])

        default_done = Path(
            "done".join(str(settings["todo-file"]).rsplit("todo", 1))
        )
        LOG.log(VERBOSE, "default done_file: %s", default_done)

        settings["done-file"] = Path.expanduser(
            Path(cfg.pop("done-file", default_done))
        )
        LOG.log(VERBOSE, "done_file: %s", settings["done-file"])

        if not settings["done-file"].is_absolute():
            settings["done-file"] = todo_dir / settings["done-file"]
            LOG.log(VERBOSE, "absolute done_file: %s", settings["done-file"])

        if cfg:
            LOG.warning("Unknown options remain in configuration!\n%s", cfg)

        return settings

    def read_lists_from_file(self) -> Tuple[List[Task], List[Task]]:
        todo = []

        try:
            with open(self.settings["todo-file"]) as file:
                for line in file:
                    todo.append(Task.from_string(line))
        except FileNotFoundError:
            pass

        done = []

        try:
            with open(self.settings["done-file"]) as file:
                for line in file:
                    done.append(Task.from_string(line))
        except FileNotFoundError:
            pass

        return todo, done

    def print_todo(self, print_indices: bool) -> None:
        oom = len(str(len(self.todo)))
        print(self.settings["todo-file"], ":", sep="")
        for i, task in enumerate(self.todo):
            index = f"{i + 1:>0{oom}}:" if print_indices else ""
            print(index, task)

    def print_done(self, print_indices: bool) -> None:
        oom = len(str(len(self.done)))
        print(self.settings["done-file"], ":", sep="")
        for i, task in enumerate(self.done):
            index = f"{i + 1:>0{oom}}:" if print_indices else ""
            print(index, task)

    def validate_index(self, index):
        if not self.todo:
            raise ValueError("No tasks to mark done!")

        try:
            index = int(index)
        except ValueError:
            raise TypeError("Indices must be integers!")

        if 1 <= index < len(self.todo):
            return index - 1

        raise ValueError(f"Indices must be between 1 and {len(self.todo)}!")

    def handle_command(self) -> None:
        command = self.args.command
        arguments = self.args.arguments

        if command is not None:
            for cmd in self.COMMAND_LIST:
                if cmd.name == command:
                    result = cmd
                    break

            else:
                raise NotImplementedError(f'"{command}" is not implemented!')

            # arguments = self.validate_arguments(result, arguments)
            attr = result.dest or result.name
            getattr(self, attr, None)(arguments)

    def default(self) -> None:
        self.print_todo(True)

    @modifies("todo")
    def do_task(self, arguments):
        if len(arguments) == 0:
            raise TypeError(
                f'"{self.name} do" requires at least one integer as argument!'
            )

        valid_indices = []
        for i in arguments:
            valid_indices.append(self.validate_index(i))

        for i in valid_indices:
            self.todo[i].complete = not self.todo[i].complete

    @no_default
    def listarchive(self, _):
        self.print_done(True)
        self.run_default = False

    def main(self) -> None:
        try:
            LOG.info(
                "Files are located at:\n%s\n%s",
                self.settings["todo-file"],
                self.settings["done-file"],
            )

            self.handle_command()

            if self.run_default:
                self.default()

            if self.modified_todo:
                print("Modified todo")

            if self.modified_done:
                print("Modified done")

        except Exception as exc:
            self.error(exc)


def main() -> None:
    STodo().main()

# TODO Case sensitivity in search
# TODO Add more logging
import argparse
import configparser
import logging
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sol
from loggingextra import VERBOSE, configure_logger

from ...task import Task
from .helpers import COMMAND_LIST, modifies, no_default, register, requires

LOG = logging.getLogger(__name__)


class STodo:
    DEFAULT_DIR = Path.expanduser(Path("~/.sol"))

    def __init__(self) -> None:
        self.parser = self.create_parser()
        try:
            self.args, arguments_in = self.parser.parse_known_args()
            self.args.arguments = arguments_in

            configure_logger(self.args.verbosity, sol.LOG_PATH, sol.__name__)
            LOG.debug(f"Command line args:\n{self.args}")

            self.settings = self.read_settings()
            LOG.debug(f"Settings:\n{self.settings}")

            self.todo, self.done = self.read_lists_from_file()

            self.run_default = True
            self.modified_todo = False
            self.modified_done = False

            self.name = Path(sys.argv[0]).name

        except Exception as exc:  # pylint: disable=broad-except
            self.error(exc)

    def error(self, exc):
        if LOG.isEnabledFor(logging.DEBUG):
            raise exc from None

        self.parser.error(exc)

    ######################################
    #    Parse command-line arguments    #
    ######################################
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

        date_mutex = parser.add_mutually_exclusive_group()
        date_mutex.add_argument(
            "-t",
            action="store_true",
            dest="prepend_date",
            help="prepend current date to added tasks.",
        )
        date_mutex.add_argument(
            "-T",
            action="store_false",
            default=False,
            dest="prepend_date",
            help="don't prepend current date to added tasks.",
        )

        # color_mutex = parser.add_mutually_exclusive_group()
        # color_mutex.add_argument(
        #     "--color", "-c", action="store_true", help="enable color mode.",
        # )

        # color_mutex.add_argument(
        #     "--plain", "-p", action="store_true", help="disable color mode.",
        # )

        command_choices: List[str] = []
        for command in COMMAND_LIST:
            if "default" not in command.aliases:
                command_choices.extend(command.aliases)

        parser.add_argument(
            "command",
            choices=sorted(command_choices),
            default=None,
            nargs="?",
            help="command to run",
        )

        # parser.add_argument(
        #     "arguments",
        #     nargs=argparse.REMAINDER,
        #     help="arguments for command",
        # )

        return parser

    #################################
    #    Read settings from file    #
    #################################

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

    ##################################
    #    Supporting functionality    #
    ##################################

    def write(self, target):
        with open(self.settings[f"{target}-file"], "w") as filename:
            for task in getattr(self, target):
                filename.write(task.to_string() + "\n")

    def print(self, tasklist, print_indices=True, name=""):
        if tasklist:
            oom = len(str(len(tasklist)))

            if name:
                print(f"{name}:")

            for i, task in enumerate(tasklist):
                index = f"{i + 1:>0{oom}}:" if print_indices else ""
                print(index, task)

    def filter_list(self, source_list, arguments):
        terms = []
        negative_terms = []

        for term in arguments:
            if term.startswith("/"):
                negative_terms.append(term[1:])
            else:
                terms.append(term)

        tasklist = []

        for task in source_list:
            if any(task.contains_term(term) for term in negative_terms):
                continue

            if all(task.contains_term(term) for term in terms):
                tasklist.append(task)

        return tasklist

    def list_tags(self, target, arguments):
        tasklist = self.filter_list(self.todo, arguments)

        tags = set()
        for task in tasklist:
            for tag in getattr(task, target):
                tags.add(tag)

        print(f"{target.capitalize()} in {self.settings['todo-file']}:")
        for tag in sorted(tags):
            print(f"\t{tag}")

    def validate_indices(self, func_name, indices):
        if len(indices) == 0:
            raise TypeError(
                f'"{self.name} {func_name}" requires at least '
                "one integer as argument!"
            )

        return [self.validate_index(i) for i in indices]

    def validate_index(self, index):
        try:
            index = int(index)
        except ValueError:
            raise TypeError("Indices must be integers!")

        if 1 <= index <= len(self.todo):
            return index - 1

        raise ValueError(f"Indices must be between 1 and {len(self.todo)}!")

    def handle_command(self) -> None:
        command = self.args.command
        arguments = self.args.arguments

        if command is not None:
            for cmd in COMMAND_LIST:
                if command in cmd.aliases:
                    result = cmd
                    break

            else:
                raise NotImplementedError(f'"{command}" is not implemented!')

            # arguments = self.validate_arguments(result, arguments)
            getattr(self, result.dest, None)(arguments)

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
                self.write("todo")

            if self.modified_done:
                self.write("done")

        except Exception as exc:  # pylint: disable=broad-except
            self.error(exc)

    ######################
    #    CLI commands    #
    ######################

    def default(self) -> None:
        self.list_todo([])

    @modifies("todo")
    @requires("todo", num_args=2, arbitrary=True)
    @register("append")
    def append(self, arguments):
        index = self.validate_indices("append", [arguments[0]])[0]

        self.todo[index].msg += " " + " ".join(arguments[1:])

    @modifies("todo", "done")
    @no_default
    @register("archive")
    def archive(self, _):
        completed = [task for task in self.todo if task.complete]
        for task in completed:
            self.todo.remove(task)
            self.done.append(task)

        self.list_all([])

    @modifies("todo")
    @register("add")
    def add_task(self, arguments):
        task = Task.from_string(" ".join(arguments))
        if self.args.prepend_date:
            task.date_created = datetime.now()

        self.todo.append(task)

    @modifies("todo")
    @register("deduplicate", "dedup")
    def deduplicate(self, _):
        new_list = []

        for task in self.todo:
            if task not in new_list:
                new_list.append(task)

        self.todo = new_list

    @modifies("todo")
    @requires("todo", num_args=1, arbitrary=True)
    @register("delete", "del", "remove", "rm")
    def delete(self, arguments):
        valid_indices = self.validate_indices("delete", arguments)

        for i in sorted(valid_indices, reverse=True):
            task = self.todo.pop(i)
            print(f"Removing task:\n    {task}")

        print()

    @modifies("todo")
    @requires("todo", num_args=1, arbitrary=True)
    @register("deprioritize", "depri", "dp")
    def deprioritize(self, arguments):
        valid_indices = self.validate_indices("deprioritize", arguments)
        for index in valid_indices:
            self.todo[index].priority = ""

    @modifies("todo")
    @register("do", "done")
    @requires("todo", num_args=1, arbitrary=True)
    def do_task(self, arguments):
        valid_indices = self.validate_indices("do", arguments)

        for i in valid_indices:
            self.todo[i].complete = not self.todo[i].complete

    @no_default
    @register("listall")
    @requires(num_args=0, arbitrary=True)
    def list_all(self, arguments):
        self.list_todo(arguments)
        self.list_done(arguments)

    @no_default
    @register("listcontexts", "listcon", "lsc")
    @requires(num_args=0, arbitrary=True)
    def list_contexts(self, arguments):
        self.list_tags("contexts", arguments)

    @no_default
    @register("listpriority", "listpri", "lsp")
    @requires(num_args=0, arbitrary=True)
    def list_priority(self, arguments):
        tasklist = self.todo

        if len(arguments) == 0:
            tasklist = [task for task in tasklist if task.priority]

        else:
            if len(arguments) > 1:
                tasklist = self.filter_list(self.todo, arguments[1:])

            expr = re.compile(f"[{arguments[0].upper()}]")

            # for task in tasklist:
            #     print(expr.match(task.priority))

            tasklist = [task for task in tasklist if expr.match(task.priority)]

        self.print(tasklist, name=self.settings["todo-file"])

    @no_default
    @register("listprojects", "listproj", "lsprj")
    @requires(num_args=0, arbitrary=True)
    def list_projects(self, arguments):
        self.list_tags("projects", arguments)

    @no_default
    @register("listdone")
    @requires(num_args=0, arbitrary=True)
    def list_done(self, arguments):
        if not arguments:
            self.print(self.done, name=self.settings["done-file"])

        else:
            tasklist = self.filter_list(self.done, arguments)
            self.print(tasklist, name=self.settings["done-file"])

    @no_default
    @register("list")
    @requires(num_args=0, arbitrary=True)
    def list_todo(self, arguments):
        if not arguments:
            self.print(self.todo, name=self.settings["todo-file"])

        else:
            tasklist = self.filter_list(self.todo, arguments)
            self.print(tasklist, name=self.settings["todo-file"])

    @modifies("todo")
    @requires("todo", num_args=2, arbitrary=True)
    @register("prepend")
    def prepend(self, arguments):
        index = self.validate_indices("prepend", [arguments[0]])[0]
        task = self.todo[index]

        task.msg = " ".join(arguments[1:]) + " " + task.msg

    @modifies("todo")
    @requires("todo", num_args=2, arbitrary=True)
    @register("priority", "pri")
    def priority(self, arguments):
        index = self.validate_indices("priority", [arguments[0]])[0]
        priority = arguments[1].upper()

        self.todo[index].priority = priority

    @modifies("todo")
    @requires("todo", num_args=2, arbitrary=True)
    @register("replace")
    def replace(self, arguments):
        index = self.validate_indices("priority", [arguments[0]])[0]
        self.todo[index] = Task.from_string(" ".join(arguments[1:]))


def main() -> None:
    STodo().main()

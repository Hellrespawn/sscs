import argparse
import configparser
import logging
from pathlib import Path

import sol
from loggingextra import VERBOSE, configure_logger

from ..task import Task

LOG = logging.getLogger(__name__)


class STodo:
    DEFAULT_DIR = Path.expanduser(Path("~/.sol"))

    def __init__(self):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        configure_logger(self.args.verbosity, sol.LOG_PATH, sol.__name__)
        LOG.debug(f"Command line args:\n{self.args}")

        self.settings = self.read_settings()
        LOG.debug(f"Settings:\n{self.settings}")

        self.todo, self.done = self.read_lists_from_file()

        self.run_default = True

    def create_parser(self):
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

        parser.add_argument(
            "command",
            # choices=[],
            default="default",
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

    def read_settings(self):
        cfg = configparser.ConfigParser()
        settings = {}

        cfg_file = (
            Path(self.args.config)
            if self.args.config
            else self.DEFAULT_DIR / "config"
        )

        try:
            with open(Path.expanduser(cfg_file)) as file:
                cfg.read_string("\n".join([f"[dummy]"] + file.readlines()))

            settings = self.parse_settings(cfg["dummy"])

        except FileNotFoundError:
            if self.args.config:
                self.parser.error(
                    f'Unable to read "{self.args.config}" as config!'
                )

        return settings

    def parse_settings(self, cfg):
        settings = {}

        todo_dir = Path.expanduser(Path(cfg.pop("todo-dir", self.DEFAULT_DIR)))
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

    def read_lists_from_file(self):
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

    def handle_command(self):
        command = self.args.command
        arguments = self.args.arguments

    def print_todo(self, print_indices):
        oom = len(str(len(self.todo)))
        print(self.settings["todo-file"], ":", sep="")
        for i, task in enumerate(self.todo):
            index = f"{i + 1:>0{oom}}:" if print_indices else ""
            print(index, task)

    def print_done(self, print_indices):
        oom = len(str(len(self.done)))
        print(self.settings["done-file"], ":", sep="")
        for i, task in enumerate(self.done):
            index = f"{i + 1:>0{oom}}:" if print_indices else ""
            print(index, task)

    def default(self):
        self.print_todo(True)

    def main(self):
        LOG.info(
            "Files are located at:\n%s\n%s",
            self.settings["todo-file"],
            self.settings["done-file"],
        )

        self.handle_command()

        if self.run_default:
            self.default()


def main():
    STodo().main()

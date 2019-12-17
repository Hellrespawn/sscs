# TODO More commands: append, prepend, separate check/uncheck, remove, archive
# TODO Support for done archive
# TODO consistent support for indices (make sscs a subclass of tasklist with)
# TODO header and footer?
import argparse
import logging
from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
from datetime import datetime

import sol

from ..tasklist import TaskList, SSCS

LOG = logging.getLogger(__name__)

Subparsers = Any


COMMAND_REGISTER = []

Command = namedtuple("Command", ["name", "type", "aliases"])


def register_command(aliases: List[str] = None, type: str = None) -> Callable:
    aliases = aliases or []
    aliases = aliases and list(aliases)

    def wrapper(method: Callable) -> Callable:
        command = Command(name=method.__name__, type=type, aliases=aliases)
        COMMAND_REGISTER.append(command)
        return method

    return wrapper


class STodo:
    COMMAND_MAP: Dict[str, str] = {}

    DEFAULT_PATHS: List[Path] = [Path.home(), sol.LOG_FOLDER.parent / "doc"]
    DEFAULT_NAMES: List[str] = ["todo", "to-do", "todo-test"]

    MODES: List[str] = ["todotxt", "sscs"]

    def __init__(self, filename: Path = None) -> None:
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

        self.parser, args = self.parse_args()

        sol.configure_logger(args.verbosity)
        LOG.debug(f"COMMAND_MAP:\n{self.COMMAND_MAP}")

        self.settings = self.read_settings(self.tasklist, args)

        if self.settings.mode == "sscs":
            self.tasklist = SSCS(self.tasklist)

        self.modified = False

    #
    # Settings
    #
    @staticmethod
    def read_settings(
        tasklist: TaskList, args: argparse.Namespace
    ) -> argparse.Namespace:
        if args.mode == "":
            try:
                mode = tasklist[1].keywords.get("mode", "")
                if mode:
                    args.mode = mode
            except IndexError:
                pass

        if not args.mode:
            args.mode = "todotxt"

        return args

    #
    # Argument Parser
    #
    @staticmethod
    def populate_parser(
        parser: argparse.ArgumentParser, type_: str
    ) -> argparse.ArgumentParser:
        if type_ is None:
            return parser

        if type_ == "index":
            parser.add_argument("selection", nargs=1, type=int)
        else:
            raise ValueError(f'Unknown parser type "{type_}"!')

        return parser

    @classmethod
    def create_subparsers(cls, subparsers: Subparsers) -> Subparsers:
        parsers = []

        for command in COMMAND_REGISTER:
            parser = subparsers.add_parser(
                command.name, aliases=command.aliases
            )
            for alias in [command.name] + command.aliases:
                if alias in cls.COMMAND_MAP:
                    raise ValueError(
                        f"{alias} is already registered to "
                        f"{cls.COMMAND_MAP[alias]}!"
                    )
                cls.COMMAND_MAP[alias] = command.name

            parser = cls.populate_parser(parser, command.type)
            parsers.append(parser)

        return parsers

    @classmethod
    def parse_args(cls) -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
        root_parser = argparse.ArgumentParser()

        root_parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        root_parser.add_argument(
            "--skip-tags",
            "-st",
            action="store_true",
            help="hide keyword tags",
        )

        root_parser.add_argument(
            "--mode",
            "-m",
            choices=cls.MODES,
            default="",
            help="set alternate modes",
        )

        subparsers = root_parser.add_subparsers(dest="command",)

        cls.create_subparsers(subparsers)

        args, extra = root_parser.parse_known_args()
        args = root_parser.parse_args(extra, args)
        args.command = args.command or ""

        return root_parser, args

    #
    # Support functions
    #
    def update_footer(self):
        if self.tasklist.footers:
            for task in self.tasklist.footers:
                msg = " ".join(task.msg.split()[-2:])
                try:
                    datetime.strptime(
                        msg,
                        "%Y-%m-%d %H:%M:%S.%f"
                    )
                except ValueError:
                    continue

                task.msg = datetime.now().strftime(
                    "c:footer Generated on %Y-%m-%d %H:%M:%S.%f"
                )
                break

    def get_index(self) -> int:
        index = self.settings.selection[0]

        if not 1 <= index <= len(self.tasklist):
            self.parser.error(
                f"Index must be in range 1 <= i <= {len(self.tasklist)}"
            )

        return index

    def run_command(self, name: str) -> Any:
        if name:
            for title in (f"{name}_{self.settings.mode}", name):
                try:
                    func = getattr(self, self.COMMAND_MAP[title])
                    break

                except AttributeError:
                    LOG.warning(f"Unable to find function {title}")
                except KeyError:
                    LOG.warning(f"Unable to find {title} in COMMAND_MAP")
            else:
                LOG.info(f"Unable to find '{name}'")

            LOG.info(f"Running command {title}")
            return func()

        else:
            LOG.info("Command is empty, so only printing")

    #
    # Commands
    #
    @register_command(["check", "do", "tick"], "index")
    def done(self) -> None:
        index = self.get_index()

        self.tasklist[index].complete = (
            "" if self.tasklist[index].complete else "x"
        )

        self.modified = True

    @register_command(["order"])
    def sort(self) -> None:
        pass

    @register_command(["delete"], "index")
    def remove(self) -> None:
        pass

    @register_command()
    def print(self) -> None:
        print(self.tasklist.to_string(True, self.settings.skip_tags))

    def main(self) -> None:
        print(self.settings)
        self.run_command(self.settings.command)
        self.run_command("print")

        if self.modified:
            if self.settings.mode == "sscs":
                self.update_footer()

            self.tasklist.to_file()


def main():
    STodo().main()

# TODO? Convert Command, Argument to dataclass
import argparse
import logging
from typing import Any, Callable, Dict, List

from .. import EXTRA_VERBOSE

LOG = logging.getLogger(__name__)


class Command:
    def __init__(self, qualname, arguments=None, aliases=None):
        self.qualname = qualname
        self.arguments = arguments or []
        self.aliases = aliases or []


class Argument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Register:
    COMMAND_REGISTER: Dict[str, "Command"] = {}

    @staticmethod
    def get_command(method: Callable) -> Command:
        command = Register.COMMAND_REGISTER.get(method.__qualname__)
        if not command:
            command = Command(qualname=method.__qualname__)
            Register.COMMAND_REGISTER[method.__qualname__] = command

        return command

    # TODO? Write tests for register_argument without command?

    @staticmethod
    def command(*aliases) -> Callable:
        def wrapper(method: Callable) -> Callable:
            command = Register.get_command(method)
            command.aliases = list(aliases)
            return method

        return wrapper

    @staticmethod
    def argument(*args, **kwargs) -> Callable:
        def wrapper(method: Callable) -> Callable:
            command = Register.get_command(method)

            command.arguments.append(Argument(*args, **kwargs))

            return method

        return wrapper

    @staticmethod
    def command_map_and_subparsers(
        instance, subparsers: Any
    ) -> Dict[str, str]:
        parsers = []
        command_map: Dict[str, str] = {"default": "default"}

        for command in Register.COMMAND_REGISTER.values():
            parts = command.qualname.split(".")
            name = parts[-1]
            prefix = ".".join(parts[:-1])
            if prefix != instance.__class__.__qualname__:
                continue

            parser = subparsers.add_parser(name, aliases=command.aliases)

            for alias in [name] + command.aliases:
                if alias in command_map:
                    raise ValueError(
                        f"{alias} is already registered to "
                        f"{command_map[alias]}!"
                    )
                command_map[alias] = name

            parser = Register.populate_parser(parser, command.arguments)
            parsers.append(parser)

        return command_map

    @staticmethod
    def populate_parser(
        parser: argparse.ArgumentParser, arguments: List[Argument]
    ) -> argparse.ArgumentParser:
        for arg in arguments:
            LOG.log(EXTRA_VERBOSE, "Adding %s: %s", arg.args, arg.kwargs)
            parser.add_argument(*arg.args, **arg.kwargs)

        return parser

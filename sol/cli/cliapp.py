# TODO? SPin off cliapp into it's own project?
# TODO? Convert Command, Argument to dataclass
import argparse
import logging
from typing import Any, Callable, Dict, List

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

COMMAND_REGISTER: Dict[str, "Command"] = {}


class Command:
    def __init__(self, qualname, arguments=None, aliases=None):
        self.qualname = qualname
        self.arguments = arguments or []
        self.aliases = aliases or []


class Argument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def get_command(method: Callable) -> Command:
    command = COMMAND_REGISTER.get(method.__qualname__)
    if not command:
        command = Command(qualname=method.__qualname__)
        COMMAND_REGISTER[method.__qualname__] = command

    return command


# TODO? Consolidate decorators into class?
# TODO? Write tests for register_argument without command?
def register_command(*aliases) -> Callable:
    def wrapper(method: Callable) -> Callable:
        command = get_command(method)
        command.aliases = list(aliases)
        return method

    return wrapper


def register_argument(*args, **kwargs) -> Callable:
    def wrapper(method: Callable) -> Callable:
        command = get_command(method)

        command.arguments.append(Argument(*args, **kwargs))

        return method

    return wrapper


class CLIApp:
    def __init__(self, common_options=None, args=None) -> None:
        self.command_map: Dict[str, str] = {"default": "default"}

        self.parser = self.create_argparser(common_options)
        args = self.parse_args(common_options, args)

        LOG.debug(f"COMMAND_MAP:\n{self.command_map}")

        self.settings = self.read_settings(args)

        LOG.debug(f"Settings:\n{self.settings}")

    @staticmethod
    def read_settings(args: argparse.Namespace) -> argparse.Namespace:
        return args

    @staticmethod
    def populate_parser(
        parser: argparse.ArgumentParser, arguments: List[Argument]
    ) -> argparse.ArgumentParser:
        for arg in arguments:
            LOG.debug("Adding %r", arg)
            parser.add_argument(*arg.args, **arg.kwargs)

        return parser

    def create_subparsers(self, subparsers: Any) -> Any:
        parsers = []
        LOG.debug(COMMAND_REGISTER)

        for command in COMMAND_REGISTER.values():
            parts = command.qualname.split(".")
            name = parts[-1]
            prefix = ".".join(parts[:-1])
            if prefix != self.__class__.__qualname__:
                continue

            parser = subparsers.add_parser(name, aliases=command.aliases)

            for alias in [name] + command.aliases:
                if alias in self.command_map:
                    raise ValueError(
                        f"{alias} is already registered to "
                        f"{self.command_map[alias]}!"
                    )
                self.command_map[alias] = name

            parser = self.populate_parser(parser, command.arguments)
            parsers.append(parser)

        return parsers

    def parse_args(self, common_options, args):
        args, extra = self.parser.parse_known_args(args)
        args = common_options.parse_args(extra, args)
        args.command = args.command or ""

        return args

    def create_argparser(
        self, common_options=None
    ) -> argparse.ArgumentParser:
        parents = common_options and [common_options]
        root_parser = argparse.ArgumentParser(parents=parents)

        subparsers = root_parser.add_subparsers(dest="command")

        self.create_subparsers(subparsers)

        return root_parser

    def run_command(self, name: str) -> Any:
        name = name or "default"
        try:
            func = getattr(self, self.command_map[name])
            return func()

        except AttributeError:
            LOG.warning(f"Unable to find function {name}")
        except KeyError:
            LOG.warning(f"Unable to find {name} in COMMAND_MAP")

        raise ValueError(f"Unable to run function {name}!")

    # def run_command(self, name: str) -> Any:
    #     if name:
    #         for title in (f"{name}_{self.settings.mode}", name):
    #             try:
    #                 func = getattr(self, self.COMMAND_MAP[title])
    #                 break

    #             except AttributeError:
    #                 LOG.warning(f"Unable to find function {title}")
    #             except KeyError:
    #                 LOG.warning(f"Unable to find {title} in COMMAND_MAP")
    #         else:
    #             LOG.info(f"Unable to find '{name}'")

    #         LOG.info(f"Running command {title}")
    #         return func()

    #     else:
    #         LOG.info("Command is empty, so only printing")

    def main(self):
        self.pre_command()
        self.run_command(self.settings.command)
        self.post_command()

    def default(self):
        pass

    def pre_command(self):
        pass

    def post_command(self):
        pass

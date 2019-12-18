import argparse
import logging
from collections import namedtuple
from typing import Any, Callable, Dict, List, Union

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

COMMAND_REGISTER = []

Command = namedtuple("Command", ["qualname", "arguments", "aliases"])


class Argument:
    def __init__(self, *names, default=None, nargs=None):
        self.names = names
        self.default = default
        self.nargs = nargs

    def __repr__(self):
        string = ", ".join(
            f"{attr}={getattr(self, attr)!r}"
            for attr in dir(self)
            if not attr.startswith("_")
        )
        return f"{type(self).__name__}({string})"


class Flag(Argument):
    def __init__(self, *names, default=None):
        super().__init__(*names, default=default, nargs=0)


def register_command(*aliases, arguments: List[Argument] = None) -> Callable:
    aliases = aliases or []  # type: ignore
    arguments = arguments or []

    def wrapper(method: Callable) -> Callable:
        command = Command(
            qualname=method.__qualname__, arguments=arguments, aliases=list(aliases)
        )
        COMMAND_REGISTER.append(command)
        return method

    return wrapper


class CLIApp:
    COMMAND_MAP: Dict[str, str] = {"default": "default"}

    def __init__(self, common_options=None) -> None:
        self.parser = self.create_argparser(common_options)
        args = self.parse_args(common_options)

        LOG.debug(f"COMMAND_MAP:\n{self.COMMAND_MAP}")

        self.settings = self.read_settings(args)

    @staticmethod
    def read_settings(args: argparse.Namespace) -> argparse.Namespace:
        return args

    @staticmethod
    def populate_parser(
        parser: argparse.ArgumentParser, arguments: List[Union[Flag]]
    ) -> argparse.ArgumentParser:
        for arg in arguments:
            LOG.debug("Adding %r", arg)
            if isinstance(arg, Flag):
                parser.add_argument(
                    *arg.names,
                    action="store_true"
                    if arg.default is False
                    else "store_false",
                )
            elif isinstance(arg, Argument):
                parser.add_argument(
                    *arg.names, default=arg.default or None, nargs=arg.nargs,
                )

        return parser

    @classmethod
    def create_subparsers(cls, subparsers: Any) -> Any:
        parsers = []
        LOG.debug(COMMAND_REGISTER)

        for command in COMMAND_REGISTER:
            parts = command.qualname.split(".")
            name = parts[-1]
            prefix = ".".join(parts[:-1])
            if prefix != cls.__qualname__:
                continue

            parser = subparsers.add_parser(
                name, aliases=command.aliases
            )

            for alias in [name] + command.aliases:
                if alias in cls.COMMAND_MAP:
                    raise ValueError(
                        f"{alias} is already registered to "
                        f"{cls.COMMAND_MAP[alias]}!"
                    )
                cls.COMMAND_MAP[alias] = name

            parser = cls.populate_parser(parser, command.arguments)
            parsers.append(parser)

        return parsers

    def parse_args(self, common_options):
        args, extra = self.parser.parse_known_args()
        args = common_options.parse_args(extra, args)
        args.command = args.command or ""

        return args

    @classmethod
    def create_argparser(cls, common_options=None) -> argparse.ArgumentParser:
        parents = common_options and [common_options]
        root_parser = argparse.ArgumentParser(parents=parents)

        subparsers = root_parser.add_subparsers(dest="command")

        cls.create_subparsers(subparsers)

        return root_parser

    def run_command(self, name: str) -> Any:
        name = name or "default"
        try:
            func = getattr(self, self.COMMAND_MAP[name])
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


class TestApp(CLIApp):
    def __init__(self):
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
            "--force",
            "-f",
        )

        super().__init__(common_options)

    @register_command("append")
    def add(self):
        print("adding")

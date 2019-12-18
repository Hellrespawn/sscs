# TODO? Spin off CLIApp into its own project?
import argparse
import logging
from typing import Any, Dict, List

from .register import Register

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


class CLIApp:
    def __init__(self, common_options=None, args=None) -> None:
        self.parser = argparse.ArgumentParser(
            parents=common_options and [common_options]
        )

        self.command_map = self.get_command_map(self.parser)
        args = self.parse_args(common_options, args)

        LOG.debug(f"command_map:\n{self.command_map}")

        self.settings = self.read_settings(args)

        LOG.debug(f"settings:\n{self.settings}")

    @staticmethod
    def read_settings(args: argparse.Namespace) -> argparse.Namespace:
        return args

    def parse_args(
        self, common_options: argparse.ArgumentParser, args_in: List[str]
    ) -> argparse.Namespace:
        args, extra = self.parser.parse_known_args(args_in)
        args = common_options.parse_args(extra, args)
        args.command = args.command or ""

        return args

    def get_command_map(self, parser) -> Dict[str, str]:
        subparsers = parser.add_subparsers(dest="command")

        command_map = Register.command_map_and_subparsers(self, subparsers)

        return command_map

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

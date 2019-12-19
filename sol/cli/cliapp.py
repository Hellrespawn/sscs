# TODO? Spin off CLIApp into its own project?
import argparse
import configparser
import logging
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List

import sol
from sol import EXTRA_VERBOSE

from .register import Register

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


class CLIApp:
    def __init__(self, common_options=None, args=None, name=None) -> None:
        self.name = name or type(self).__name__.lower()

        self.parser = argparse.ArgumentParser(
            parents=common_options and [common_options]
        )

        self.command_map = self.get_command_map(self.parser)
        args = self.parse_args(common_options, args)

        self.config_dir: Path

        self.settings = self.read_settings(args)

        LOG.debug(f"command_map:\n{self.command_map}")
        LOG.debug(f"settings:\n{self.settings}")

    def file_locations(self):
        directories: List[Path] = [
            Path.home(),
            Path.home() / ("." + self.name),
            Path.home() / ".config",
            Path("etc") / self.name,
            Path(sol.__file__).parents[1] / "doc",
        ]

        extensions = ["cfg", "ini"]

        names = [
            name + "." + ext
            for name in [self.name, "." + self.name]
            for ext in extensions
        ]

        locations = [
            dir / name
            for dir in directories
            for name in names
            if (dir / name).exists()
        ]
        LOG.log(
            EXTRA_VERBOSE, "Possible file locations:\n%s", pformat(locations)
        )
        return locations

    def read_settings(self, args: argparse.Namespace) -> argparse.Namespace:
        cfg = configparser.ConfigParser()

        for filename in self.file_locations():
            try:
                with open(filename, "r") as file:
                    LOG.debug("Config found at %s", filename)
                    cfg.read_string(
                        "\n".join([f"[{self.name}]"] + file.readlines())
                    )
                    self.config_dir = filename.parent
                    break
            except FileNotFoundError:
                pass

        self.config_dir = self.config_dir or self.file_locations()[0]

        for section in cfg.sections():
            for option in cfg.options(section):
                setattr(args, option, cfg.get(section, option))

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

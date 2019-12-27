import argparse
import configparser
import logging
from pathlib import Path

import sol
from loggingextra import configure_logger, VERBOSE

from ..task import Task

LOG = logging.getLogger(__name__)


class STodo:
    DEFAULT_FOLDER = Path("~/.sol")

    def __init__(self):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        configure_logger(self.args.verbosity, sol.LOG_PATH, sol.__name__)
        LOG.log(VERBOSE, f"Command line args:\n{self.args}")

        self.settings = self.read_settings()

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
                f"default {self.DEFAULT_FOLDER / 'config'}."
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

        cfg_file = self.args.config and Path(self.args.config) or self.DEFAULT_FOLDER / "config"

        try:
            with open(Path.expanduser(cfg_file)) as file:
                cfg.read_string(
                    "\n".join([f"[stodo]"] + file.readlines())
                )

            for section in cfg.sections():
                for option in cfg.options(section):
                    settings[option] = cfg.get(section, option)

        except FileNotFoundError:
            if self.args.config:
                self.parser.error(
                    f'Unable to read "{self.args.config}" as config!'
                )

        LOG.log(VERBOSE, f"Settings from file:\n{settings}")
        return settings

    def main(self):
        pass


def main():
    STodo().main()

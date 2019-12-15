# TODO? Try opening gitignore
import argparse
import logging
import re
import sys
from datetime import datetime
from os.path import getsize
from pathlib import Path
from typing import List

from sol import configure_logger
from sol.task import Task
from sol.tasklist import TaskList

LOG = logging.getLogger(__name__)


class SSCS:
    CATEGORIES = ("TODO?", "TODO", "IDEA", "FIXME")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    BLACKLIST = [".mypy_cache", ".git", "__pycache__", ".log"]
    WHITELIST = [".py"]

    def __init__(
        self, *, whitelist: List[str] = None, blacklist: List[str] = None
    ) -> None:
        self.whitelist = (whitelist or []) + self.WHITELIST
        self.blacklist = (blacklist or []) + self.BLACKLIST

        self.tasklist = TaskList()
        self.errors: dict = {}

    def line_to_task(self, string, line_no, filename):
        categories = "|".join(self.CATEGORIES).replace("?", "\\?")
        expr = r".*?(?P<category>" + categories + r")\s*(?P<msg>.*)"

        match = re.match(expr, string.strip())
        if match:
            category = match.group("category")
            msg = match.group("msg")
            filename = filename.relative_to(Path.cwd())

            msg = f"cat:{category:<5} ln:{line_no:>03} @{filename} {msg}"

            return Task(msg)

        raise ValueError(f'Unable to parse "{string.strip()}" as task')

    def parse_source_file(self, filename: Path) -> None:
        with open(filename, "r") as file:
            try:
                for i, line in enumerate(file):
                    for category in self.CATEGORIES:
                        if category in line:
                            try:
                                self.tasklist.append(
                                    self.line_to_task(line, i, filename)
                                )
                            except ValueError as exc:
                                tpl = (i + 1, exc)
                                try:
                                    self.errors[str(filename)].append(tpl)
                                except KeyError:
                                    self.errors[str(filename)] = [tpl]
                            break
            except UnicodeDecodeError:
                pass

    def recurse_project(self, path: Path, i: int = -1) -> None:
        if i == -1:
            i = self.MAX_RECURSION
        elif i == 0:
            LOG.debug(f"Exceeded max recursion depth @ {path}")
            return

        path = Path(path)

        for filename in path.iterdir():
            if any([item in str(filename) for item in self.blacklist]):
                continue

            if filename.is_dir():
                self.recurse_project(filename, i - 1)

            else:
                if getsize(filename) > self.MAX_SIZE:
                    LOG.debug(f"{filename} is too big!")
                    continue

                if self.whitelist:
                    for item in self.whitelist:
                        if item in str(filename):
                            break

                    else:
                        continue

                self.parse_source_file(filename)

    def parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            dest="verbosity",
            help="increase verbosity",
            default=0,
        )

        parser.add_argument("--output", "-o", help="Optional output file")

        parser.add_argument(
            "--force", "-f", action="store_true", help="Overwrite output file"
        )

        parser.add_argument("path", nargs="?", default=Path.cwd())

        return parser.parse_args()

    @staticmethod
    def error(string: str) -> None:
        print(string)
        sys.exit()

    def main(self) -> None:
        args = self.parse_args()

        configure_logger(args.verbosity)

        self.recurse_project(Path(args.path))

        self.tasklist.insert(
            0, Task(f"cat:header Generated on {datetime.now()}")
        )

        if self.errors:
            LOG.info("Logging errors:")
            for filename in self.errors:
                if LOG.isEnabledFor(logging.INFO):
                    # pylint: disable=logging-not-lazy
                    LOG.info(
                        f"{filename!s}: "
                        + ", ".join(str(i) for i in self.errors[filename])
                    )
                    # pylint: enable=logging-not-lazy

        if args.output is None:
            print(self.tasklist)

        else:
            filename = Path(args.output)
            if filename.exists() and not args.force:
                sys.exit(f"{filename} exists! Did you mean to use --force?")

            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w") as file:
                file.write(str(self.tasklist))

            print(f"Wrote to {filename!s}")


def main():
    SSCS().main()

import argparse
import logging
import sys
from os.path import getsize
from pathlib import Path
from typing import List

from sol import configure_logger
from sol.task import CodeTask
from sol.taskdict import TaskDict

LOG = logging.getLogger(__name__)


class SSCS:
    CATEGORIES = ("TODO", "TODO?", "IDEA", "FIXME")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    BLACKLIST = [".mypy_cache", ".git"]

    def __init__(
        self, *, whitelist: List[str] = None, blacklist: List[str] = None
    ) -> None:
        self.whitelist = whitelist or []
        self.blacklist = (blacklist or []) + self.BLACKLIST

        self.taskdict = TaskDict()
        self.errors: dict = {}

    def parse_source_file(self, filename: Path) -> None:
        with open(filename, "r") as file:
            try:
                for i, line in enumerate(file):
                    for category in self.CATEGORIES:
                        if category in line:
                            try:
                                self.taskdict.append(
                                    filename,
                                    CodeTask.from_comment_string(i + 1, line),
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

    def taskdict_from_project(self, path: Path, i: int = -1) -> None:
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
                self.taskdict_from_project(filename, i - 1)

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

    def main(self) -> None:
        args = self.parse_args()

        configure_logger(args.verbosity)

        self.taskdict_from_project(Path(args.path))

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
            print(self.taskdict)
        else:
            filename = Path(args.output)
            if filename.exists() and not args.force:
                sys.exit(f"{filename} exists! Did you mean to use --force?")

            with open(filename, "w") as file:
                file.write(str(self.taskdict))


def main():
    SSCS().main()

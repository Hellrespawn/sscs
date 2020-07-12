# TODO? append instead of overwrite flag
import argparse
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from os.path import getsize
from pathlib import Path
from typing import DefaultDict, List, Tuple

import sol
from hrshelpers.logging import configure_logger
from sol.task import Task

LOG = logging.getLogger(__name__)


class SSCS:
    CATEGORIES = ("UPSTREAM", "IDEA", "TODO?", "TODO", "FIXME")  # sscs: skip
    PRIORITIES = ("D", "C", "C", "B", "A")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    ALLOWLIST = [".py", ".ebnf", ".md", ".txt", ".rs", ".sh"]
    DENYLIST = ["todo.txt"]

    SKIP = "sscs: skip"

    def __init__(self, *, allowlist: List[str] = None,) -> None:
        self.allowlist = (allowlist or []) + self.ALLOWLIST

        self.tasklist: List[Task] = []
        self.errors: dict = {}

    @classmethod
    def parse_match(cls, line_no, filename, match):
        category = match.group("category")
        priority = cls.PRIORITIES[cls.CATEGORIES.index(category)]
        msg = match.group("msg")
        try:
            printname = filename.resolve().relative_to(Path.cwd())

        except ValueError:
            i = 0
            while True:
                try:
                    printname = filename.resolve().relative_to(
                        Path.cwd().parents[i]
                    )
                    break
                except ValueError:
                    i += 1

        project, context = printname.parts[0], Path(*printname.parts[1:])

        msg = f"c:{category} +{project} @{context} ln:{line_no + 1:>03} {msg}"

        return Task(msg, priority=priority)

    @classmethod
    def parse_source_file(
        cls, filename: Path
    ) -> Tuple[List, DefaultDict[str, List[int]]]:
        categories = "|".join(cls.CATEGORIES).replace("?", "\\?")
        expr = re.compile(
            r".*?(?P<category>" + categories + r")\s*(?P<msg>.*)"
        )

        tasklist = []
        errors: DefaultDict[str, List[int]] = defaultdict(list)

        with open(filename, "r") as file:
            try:
                for i, line in enumerate(file):
                    if cls.SKIP in line:
                        if i == 0:
                            return [], defaultdict(list)

                        continue

                    match = expr.match(line.strip())

                    if not match:
                        errors[str(filename)].append(i + 1)
                        continue

                    tasklist.append(cls.parse_match(i, filename, match))

            except UnicodeDecodeError:
                pass

        return tasklist, errors

    def recurse_project(
        self, path: Path, i: int = 0
    ) -> Tuple[List, DefaultDict[str, List[int]]]:
        tasklist = []
        errors: DefaultDict[str, List[int]] = defaultdict(list)

        for filename in path.iterdir():
            if filename.is_dir() and i < self.MAX_RECURSION:
                new_tasks, new_errors = self.recurse_project(filename, i + 1)
                tasklist.extend(new_tasks)
                errors.update(new_errors)

            else:
                if filename.name in self.DENYLIST:
                    continue

                if getsize(filename) > self.MAX_SIZE:
                    LOG.debug("%s is too big!", filename)
                    continue

                for item in self.allowlist:
                    if item in filename.suffix:
                        new_tasks, new_errors = self.parse_source_file(
                            filename
                        )
                        tasklist.extend(new_tasks)
                        errors.update(new_errors)
                        break

        return tasklist, errors

    @staticmethod
    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            dest="verbosity",
            help="increase verbosity",
            default=0,
        )

        parser.add_argument(
            "--enumerate",
            action="store_true",
            help="Include line numbers in output.",
        )

        parser.add_argument("path", nargs="?", default=Path.cwd())

        return parser.parse_args()

    @staticmethod
    def error(string: str) -> None:
        print(string)
        sys.exit()

    def main(self) -> None:
        args = self.parse_args()

        configure_logger(args.verbosity, sol.LOG_PATH, sol.__name__)

        self.tasklist, self.errors = self.recurse_project(Path(args.path))
        self.tasklist.sort()

        self.tasklist = [Task(f"header:options mode:sol")] + self.tasklist

        self.tasklist.append(
            Task(f"footer:time Generated on {datetime.now()}")
        )

        if self.errors:
            LOG.info("Logging errors:")
            for filename in self.errors:
                if LOG.isEnabledFor(logging.INFO):
                    # pylint: disable=logging-not-lazy
                    LOG.info(
                        f"{filename!s}: "
                        ", ".join(str(i) for i in self.errors[filename])
                    )
                    # pylint: enable=logging-not-lazy

        for i, task in enumerate(self.tasklist):
            string = task.to_string()
            if args.enumerate:
                string = f"{i + 1}: {string}"
            print(string)


def main():
    SSCS().main()

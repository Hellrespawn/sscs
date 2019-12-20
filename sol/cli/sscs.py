# TODO? Try opening gitignore
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
from sol.logger import configure_logger
from sol.task import Task
from sol.tasklist import TaskList

LOG = logging.getLogger(__name__)


class SSCS:
    CATEGORIES = ("IDEA", "TODO?", "TODO", "FIXME")  # sscs: skip
    PRIORITIES = ("C", "C", "B", "A")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    WHITELIST = [".py", ".ebnf", ".md"]

    SKIP = "sscs: skip"

    def __init__(self, *, whitelist: List[str] = None,) -> None:
        self.whitelist = (whitelist or []) + self.WHITELIST

        self.tasklist = TaskList()
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
    ) -> Tuple[TaskList, DefaultDict[str, List[int]]]:
        categories = "|".join(cls.CATEGORIES).replace("?", "\\?")
        expr = re.compile(
            r".*?(?P<category>" + categories + r")\s*(?P<msg>.*)"
        )

        tasklist = TaskList()
        errors: DefaultDict[str, List[int]] = defaultdict(list)

        with open(filename, "r") as file:
            try:
                for i, line in enumerate(file):
                    if cls.SKIP in line:
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
    ) -> Tuple[TaskList, DefaultDict[str, List[int]]]:
        path = Path(path)

        tasklist = TaskList()
        errors: DefaultDict[str, List[int]] = defaultdict(list)

        for filename in path.iterdir():
            if filename.is_dir() and i < self.MAX_RECURSION:
                new_tasks, new_errors = self.recurse_project(filename, i + 1)
                tasklist.extend(new_tasks)
                errors.update(new_errors)

            else:
                if getsize(filename) > self.MAX_SIZE:
                    LOG.debug(f"{filename} is too big!")
                    continue

                for item in self.whitelist:
                    if item in filename.suffix:
                        new_tasks, new_errors = self.parse_source_file(
                            filename
                        )
                        tasklist.extend(new_tasks)
                        errors.update(new_errors)
                        break

        return tasklist, errors

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

        configure_logger(
            args.verbosity, sol.LOG_PATH, sol.__name__, sol.LOG_FORMAT
        )

        self.tasklist, self.errors = self.recurse_project(Path(args.path))
        self.tasklist.sort()

        self.tasklist.appendleft(Task(f"header:options mode:sol"))

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

        if args.output is None:
            print(self.tasklist.to_string(print_index=True))

        else:
            output = Path(args.output)
            if output.exists() and not args.force:
                sys.exit(f"{output} exists! Did you mean to use --force?")

            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as file:
                file.write(str(self.tasklist))

            print(f"Wrote to {output!s}")


def main():
    SSCS().main()

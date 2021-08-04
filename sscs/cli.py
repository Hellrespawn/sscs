import argparse
import re
from collections import defaultdict
from datetime import datetime
from os.path import getsize
from pathlib import Path
from typing import DefaultDict, List, Tuple

from rich.console import Console, RenderableType
from rich.table import Table

from sscs.task import Task

from .profile import Profile

PROFILES = {
    "rust": Profile(
        "rust",
        ["Cargo.toml", "Cargo.lock"],
        denied_directories=["target", ".git"],
        denied_extensions=[".log"],
        denied_files=["todo.txt"],
    ),
    "python": Profile(
        "python",
        ["pyproject.toml", "Pipfile", "setup.py"],
        denied_directories=[".git", ".mypy_cache", ".venv"],
        denied_extensions=[".log"],
        denied_files=["todo.txt"],
    ),
}


def calculate_profile(path: Path) -> Profile:
    for profile in PROFILES.values():
        for indicator in profile.indicator_files:
            if (path / Path(indicator)).is_file():
                return profile

    raise ValueError(f"Unable to calculate profile for {path}")


class SSCS:
    CATEGORIES = ("UPSTREAM", "IDEA", "TODO?", "TODO", "FIXME")  # sscs: skip
    PRIORITIES = ("D", "C", "C", "B", "A")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    SKIP = "sscs: skip"

    def __init__(
        self, profile: Profile, path: Path, ascii_mode: bool = False
    ) -> None:
        self.profile = profile
        self.path = path
        self.ascii_mode = ascii_mode

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
        self, path: Path, i: int
    ) -> Tuple[List, DefaultDict[str, List[int]]]:
        tasklist = []
        errors: DefaultDict[str, List[int]] = defaultdict(list)

        if i <= 0:
            return tasklist, errors

        for filename in path.iterdir():
            if filename.is_dir():
                if self.profile.is_dir_allowed(filename):
                    new_tasks, new_errors = self.recurse_project(
                        filename, i - 1
                    )
                    tasklist.extend(new_tasks)
                    errors.update(new_errors)

            else:
                if getsize(filename) > self.MAX_SIZE:
                    continue

                elif self.profile.is_file_allowed(filename):
                    new_tasks, new_errors = self.parse_source_file(filename)
                    tasklist.extend(new_tasks)
                    errors.update(new_errors)

        return tasklist, errors

    def to_string_ascii(self) -> RenderableType:
        self.tasklist.append(
            Task(
                f"footer:time Generated {str(datetime.now()).split('.')[0]} profile:{self.profile.name}"
            )
        )

        output = "\n".join(task.to_string() for task in self.tasklist)

        self.tasklist.pop()

        return output

    def to_string_rich(self) -> RenderableType:
        table = Table(show_footer=True, show_header=False)

        table.add_column(
            footer=f"Generated on {str(datetime.now()).split('.')[0]}, Profile: {self.profile.name}"
        )

        tasklists = (
            [
                task
                for task in self.tasklist
                if task.keywords["c"] == "FIXME"  # sscs: skip
            ],
            [
                task
                for task in self.tasklist
                if task.keywords["c"] == "TODO"  # sscs: skip
            ],
            [
                task
                for task in self.tasklist
                if task.keywords["c"] in ("TODO?", "IDEA")  # sscs: skip
            ],
            [
                task
                for task in self.tasklist
                if task.keywords["c"] == "UPSTREAM"  # sscs: skip
            ],
        )

        for tasklist in tasklists:
            for i, task in enumerate(tasklist):
                end_section = False

                if i == len(tasklist) - 1:
                    end_section = True

                table.add_row(task.to_string(), end_section=end_section)

        return table

    def to_string(self) -> RenderableType:
        if self.ascii_mode:
            return self.to_string_ascii()

        return self.to_string_rich()

    def main(self) -> None:
        self.tasklist, self.errors = self.recurse_project(
            Path(self.path), self.MAX_RECURSION
        )
        self.tasklist.sort()

        console = Console(highlight=False)

        console.print(self.to_string())


def main():
    args = parse_args()
    profile = PROFILES.get(args.profile) or calculate_profile(args.path)
    SSCS(profile, args.path, args.ascii).main()


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
        "--ascii",
        action="store_true",
        help="Output in ascii mode.",
    )

    parser.add_argument(
        "--profile",
        "-p",
        help="Manually select profile",
    )

    parser.add_argument("path", nargs="?", default=Path.cwd())

    return parser.parse_args()

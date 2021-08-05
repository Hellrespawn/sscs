import argparse
import re
from collections import defaultdict
from datetime import datetime
from os.path import getsize
from pathlib import Path
from typing import DefaultDict, List, Tuple

import toml
from rich.console import Console, RenderableType
from rich.table import Table

from sscs.task import Task

from .profile import Profile


class SSCS:
    CATEGORIES = ("UPSTREAM", "IDEA", "TODO?", "TODO", "FIXME")  # sscs: skip
    PRIORITIES = ("D", "C", "C", "B", "A")

    MAX_RECURSION = 4
    MAX_SIZE = 1024 ** 2  # 1 MB

    SKIP = "sscs: skip"

    def __init__(
        self, profile: Profile, path: Path, rich_mode: bool = False
    ) -> None:
        self.profile = profile
        self.path = path
        self.rich_mode = rich_mode

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
        tasklist: List[Task] = []
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

                if self.profile.is_file_allowed(filename):
                    new_tasks, new_errors = self.parse_source_file(filename)
                    tasklist.extend(new_tasks)
                    errors.update(new_errors)

        return tasklist, errors

    def to_string_ascii(self) -> RenderableType:
        date, time = (
            str(datetime.now())
            .split(".", maxsplit=1)[0]
            .split(" ", maxsplit=1)
        )

        self.tasklist.append(
            Task(
                f"footer:gen  date:{date} time:{time} profile:{self.profile.name}"
            )
        )

        output = "\n".join(task.to_string() for task in self.tasklist)

        self.tasklist.pop()

        return output

    def to_string_rich(self) -> RenderableType:
        table = Table(show_footer=True, show_header=False)

        time = str(datetime.now()).split(".", maxsplit=1)[0]

        table.add_column(
            footer=f"Generated on {time} with profile: {self.profile.name}"
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
        if self.rich_mode:
            return self.to_string_rich()

        return self.to_string_ascii()

    def main(self) -> None:
        self.tasklist, self.errors = self.recurse_project(
            Path(self.path), self.MAX_RECURSION
        )
        self.tasklist.sort()

        console = Console()

        console.print(self.to_string())


def main():
    with open(Path(__file__).parent / "profiles.toml") as file:
        toml_dict = toml.loads(file.read())

    profiles = {}

    for name, profile_dict in toml_dict.items():
        profile = Profile("", [])
        profile.__dict__.update(profile_dict)

        profiles[name] = profile

    args = parse_args()

    if args.profile:
        selected_profile = profiles.get(args.profile)
        if not selected_profile:
            print(f"No such profile: {args.profile}! Profiles:")
            print("\t" + ", ".join(profiles.keys()))
            return

    else:
        for profile in profiles.values():
            for indicator in profile.indicator_files:
                if (args.path / Path(indicator)).is_file():
                    selected_profile = profile
                    break
            else:
                continue

            # If the inner break does not occur, the else clause does, and the
            # the inner loop hits `continue`. If the inner break *does* occur
            # the continue is skipped and the outer break is hit.
            break

        else:
            print(f"Unable to calculate profile for {args.path}, using default")
            selected_profile = profiles["default"]

    SSCS(selected_profile, args.path, args.rich).main()


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
        "--rich",
        action="store_true",
        help="Output rich text.",
    )

    parser.add_argument(
        "--profile",
        "-p",
        help="Manually select profile",
    )

    parser.add_argument("path", nargs="?", default=Path.cwd())

    return parser.parse_args()

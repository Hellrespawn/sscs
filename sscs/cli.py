import argparse
import re
from datetime import datetime
from os.path import getsize
from pathlib import Path
from typing import Dict, List

import toml
from rich.console import Console


from sscs.task import Task, TaskTheme, TaskHighlighter

from .profile import Profile

MAX_RECURSION = 4
MAX_SIZE = 1024 ** 2  # 1 MB
SKIP_STRING = "sscs: skip"


CONSOLE = Console(highlighter=TaskHighlighter(), theme=TaskTheme)


class FileParser:
    def __init__(self, profile: Profile) -> None:
        self.profile = profile

        self.tasklist: List[Task] = []

    def parse_match(
        self, line_no: int, filename: Path, identifier: str, string: str
    ) -> Task:
        identifier = identifier.strip()
        task = Task.from_string(string.strip())

        if len(self.profile.identifiers) > 1:
            task.priority = chr(
                ord("A") + self.profile.identifiers.index(identifier)
            )

        prefix = ""

        if len(self.profile.identifiers) > 1:
            prefix += f"id:{identifier} "

        task.msg = f"{prefix}@{filename.name} ln:{line_no + 1:>03} {task.msg}"

        return task

    def parse_source_file(self, filename: Path) -> List[Task]:
        # Anything until and identifier, followed by anything that's not a
        # word, followed by the rest of the string.
        #
        # \W is added to every identifier to disambiguate between
        # TODO and TODO? sscs:skip
        identifiers = "|".join(
            f"{c}\\W" for c in self.profile.identifiers
        ).replace("?", "\\?")

        expr = re.compile(
            r".*?(?P<identifier>" + identifiers + r")(?P<string>.*)"
        )

        tasklist = []

        with open(filename, "r") as file:
            try:
                for i, line in enumerate(file.read().strip().split("\n")):
                    if SKIP_STRING in line:
                        if i == 0:
                            return []

                        continue

                    match = expr.match(line.strip())

                    if not match:
                        continue

                    tasklist.append(
                        self.parse_match(
                            i,
                            filename,
                            match.group("identifier"),
                            match.group("string"),
                        )
                    )

            except UnicodeDecodeError:
                pass

        return tasklist

    def recurse_project(self, path: Path, i: int) -> List[Task]:
        tasklist: List[Task] = []

        if i <= 0:
            return tasklist

        for filename in path.iterdir():
            if filename.is_dir():
                if self.profile.is_dir_allowed(filename):
                    new_tasks = self.recurse_project(filename, i - 1)
                    tasklist.extend(new_tasks)

            else:
                if getsize(filename) > MAX_SIZE:
                    continue

                if self.profile.is_file_allowed(filename):
                    new_tasks = self.parse_source_file(filename)
                    tasklist.extend(new_tasks)

        return tasklist

    def print_tasklist(self, tasklist: List[Task]) -> None:
        date = (
            str(datetime.now()).split(".", maxsplit=1)[0]
        )

        tasklist.append(
            Task(
                (
                    f"footer:true date:\"{date}\" "
                    + f"profile:{self.profile.name}"
                )
            )
        )

        output = "\n".join(task.to_string() for task in tasklist)

        tasklist.pop()

        CONSOLE.print(output)


def main():
    args = parse_args()

    file_parser = FileParser(select_profile(args.path, args.profile))

    tasklist = file_parser.recurse_project(Path(args.path), MAX_RECURSION)

    if tasklist:
        tasklist.sort()

        file_parser.print_tasklist(tasklist)

    else:
        print("You've done everything that needs doing! 👍")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile",
        "-p",
        help="Manually select profile",
    )

    parser.add_argument(
        "path", nargs="?", default=Path.cwd(), help="Path to start search in."
    )

    return parser.parse_args()


def select_profile(path: Path, name: str = None) -> Profile:
    profiles = get_profiles()

    if name:
        try:
            return profiles[name]
        except KeyError:
            raise ValueError(
                f"No such profile: {name}! Profiles:"
                + "\t"
                + ", ".join(profiles.keys())
            ) from None

    for profile in profiles.values():
        for indicator in profile.indicator_files:
            if (path / Path(indicator)).is_file():
                return profile

    # print(
    #     f"Unable to determine profile for {path}, using default"
    # )
    return profiles["default"]


def get_profiles() -> Dict[str, Profile]:
    with open(Path(__file__).parent / "profiles.toml") as file:
        toml_dict = toml.loads(file.read())

    profiles = {}

    for name, profile_dict in toml_dict.items():
        profile = Profile("", [], [])
        profile.__dict__.update(profile_dict)

        profiles[name] = profile

    return profiles

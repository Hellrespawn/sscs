import logging
import textwrap
from datetime import datetime
from pathlib import Path

from .task import task_from_string
from .tasklist import TaskList

LOG = logging.getLogger(__name__)


class TaskDict:
    def __init__(self, filepath=None) -> None:
        self.filepath = filepath
        self.taskdict: dict = {}

    def __str__(self) -> str:
        # TODO Move this to settings
        indent = "  "

        string = f"# Generated on: {datetime.now()}\n"

        for name, tasklist in self.taskdict.items():
            string += (
                name + ":\n" + textwrap.indent(str(tasklist), indent) + "\n\n"
            )

        return string

    def append(self, category, task):
        tasklist = self.taskdict.get(category, None)

        if not tasklist:
            tasklist = TaskList()
            self.taskdict[category] = tasklist

        try:
            tasklist.append(task)
        except TypeError as exc:
            raise exc from None

    @classmethod
    def from_file(cls, filepath) -> "TaskDict":
        filepath = Path(filepath)

        try:
            with open(filepath, "r") as file:
                taskdict = TaskDict()

                category = "@line 1"

                for i, line in enumerate(file):
                    line = line.strip()

                    if line.startswith("#"):
                        continue

                    if not line:
                        category = f"@line {i}"
                        continue

                    try:
                        task = task_from_string(line)
                        try:
                            taskdict.append(category, task)
                        except TypeError:
                            # TODO Handle mixed tasklist
                            category = f"@line {i}"
                            taskdict.append(category, task)

                    except ValueError:
                        if line.endswith(":"):
                            category = line[:-1]
                        else:
                            category = line
            taskdict.filepath = filepath
            return taskdict

        except FileNotFoundError as exc:
            raise exc from None

    def to_file(self, filename) -> None:
        filename = Path(filename)

        with open(filename, "w") as file:
            file.write(str(self))

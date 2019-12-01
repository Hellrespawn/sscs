import textwrap
from datetime import datetime
import logging

from .task import Task, CodeTask
from .tasklist import TaskList, CodeTaskList

LOG = logging.getLogger(__name__)


class TaskDict:
    def __init__(self) -> None:
        self.taskdict = {}

    def __str__(self) -> None:
        # TODO Move this to settings
        indent = "  "

        string = ""

        for name, tasklist in self.taskdict.items():
            string += name + ":\n" + textwrap.indent(
                str(tasklist),
                indent
            ) + "\n"

        return string.rstrip()

    def append(self, category, task):
        tasklist = self.taskdict.get(category, None)

        if not tasklist:
            if isinstance(task, Task):
                tasklist = TaskList()
            elif isinstance(task, CodeTask):
                tasklist = CodeTaskList()
            else:
                raise TypeError(f"No TaskList associated with {type(task)}")

            self.taskdict[category] = tasklist
            self.taskdict = {
                key: self.taskdict[key] for key in sorted(self.taskdict)
            }

        tasklist.append(task)

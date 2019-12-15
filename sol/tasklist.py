import logging
from typing import Iterable

from .builder import Attr, Builder
from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(list):
    @property
    def filter(self):
        return Builder(
            self._filter,
            (
                Attr("case_sens"),
                Attr("strict"),
                Attr("project", 1),
                Attr("context", 1),
            ),
        )

    def __str__(self) -> str:
        return "\n".join(str(task) for task in self)

    @classmethod
    def from_iterable(cls, iterable: Iterable[str]) -> "TaskList":
        tasklist = cls()

        for string in iterable:
            tasklist.append(Task.from_string(string.strip()))

        return tasklist

    def _filter(self, search, *, project, context, strict=False, case_sens=False):
        if project:
            target = "projects"

        elif context:
            target = "contexts"

        if case_sens:
            search = search.lower()

        results = TaskList()

        for task in self:
            for item in getattr(task, target):
                if case_sens:
                    item = item.lower()

                if strict:
                    if search == item:
                        results.append(task)
                else:
                    if search in item:
                        results.append(task)

        return results

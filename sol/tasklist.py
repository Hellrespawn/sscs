import logging
from typing import Iterable

from .builder import Builder
from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(list):
    filter = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter = Builder(self._filter)

    def __str__(self) -> str:
        return "\n".join(str(task) for task in self)

    # def append(self, item):
    #     LOG.debug(f'Appending: {item}')
    #     super().append(item)

    @classmethod
    def from_iterable(cls, iterable: Iterable[str]) -> "TaskList":
        tasklist = cls()

        for string in iterable:
            tasklist.append(Task.from_string(string.strip()))

        return tasklist

    def _filter(
        self,
        search: str,
        *,
        project_1: bool,
        context_1: bool,
        strict: bool,
        case_sens: bool
    ):
        if project_1:
            target = "projects"

        elif context_1:
            target = "contexts"

        if not case_sens:
            search = search.lower()

        results = TaskList()

        for task in self:
            for item in getattr(task, target):
                if not case_sens:
                    item = item.lower()

                if strict:
                    if search == item:
                        results.append(task)
                else:
                    if search in item:
                        results.append(task)

        return results

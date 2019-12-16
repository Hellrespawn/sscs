import logging
from pathlib import Path
from typing import Iterable

from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(list):
    def __init__(self, *args, **kwargs):
        self.filename: Path = None
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.to_string()

    def to_file(self):
        if not self.filename:
            raise AttributeError("TaskList doesn't have a filename!")

        with open(self.filename, "w") as file:
            file.write(self.to_string())

    def to_string(self, print_index: bool = False, hide_tags: bool = False):
        string = ""

        if print_index:
            oom = len(str(len(self)))
            string = "\n".join(
                f"{i + 1:>0{oom}}: {task.to_string(hide_tags)}"
                for i, task in enumerate(self)
            )
        else:
            string = "\n".join(task.to_string(hide_tags) for task in self)

        return string

    @classmethod
    def from_file(cls, filename: Path) -> "TaskList":

        with open(filename, "r") as file:
            tasklist = cls.from_iterable(file)
            tasklist.filename = filename
            return tasklist

    @classmethod
    def from_iterable(cls, iterable: Iterable[str]) -> "TaskList":
        tasklist = cls()

        for string in iterable:
            string = string.strip()
            if string:
                tasklist.append(Task.from_string(string))

        return tasklist

    def _filter_var(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> "TaskList":
        if not case_sens:
            search = search.lower()

        results = TaskList()

        for task in self:
            tgt = getattr(task, target)
            if not case_sens:
                tgt = tgt.lower()

            if (strict and search == tgt) or (not strict and search in tgt):
                results.append(task)

        return results

    def _filter_iterable(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> "TaskList":
        if not case_sens:
            search = search.lower()

        results = TaskList()

        for task in self:
            for item in getattr(task, target):
                if not case_sens:
                    item = item.lower()

                if (strict and search == item) or (
                    not strict and search in item
                ):
                    results.append(task)

        return results

    def filter(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> "TaskList":
        if target in ("context", "project"):
            results = self._filter_iterable(
                search, target + "s", strict, case_sens
            )
        if target in ("complete", "msg", "priority"):
            results = self._filter_var(
                search, target + "s", strict, case_sens
            )
        # elif target == "date":
        #     pass
        else:
            raise ValueError(f'Unable to filter by "{target}"')

        results.filename = self.filename
        return results

    def order(self, reverse: bool = False) -> "TaskList":
        results = TaskList(sorted(self, reverse=reverse))
        results.filename = self.filename
        return results

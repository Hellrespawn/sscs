import logging
from collections.abc import MutableSequence
from pathlib import Path
from typing import Iterable, List, Union

from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(MutableSequence):
    def __init__(self, iterable=None, filename=None):
        self.filename = filename
        self._container = []
        if iterable:
            for elem in iterable:
                self.append(elem)

    def __str__(self) -> str:
        return self.to_string()

    def __delitem__(self, key):
        self._container.__delitem__(key)

    def __getitem__(self, key):
        return self._container.__getitem__(key)

    def __setitem__(self, key, value):
        self._container.__setitem__(key, value)

    def __len__(self):
        return self._container.__len__()

    def insert(self, index, value):
        self._container.insert(index, value)

    def appendleft(self, task):
        self.insert(0, task)

    def popright(self):
        return self._container.pop(len(self))

    def safe_get(self, index, default=None):
        try:
            return self[index - 1]
        except IndexError:
            return default

    def safe_pop(self, index, default=None):
        try:
            return self.pop(index - 1)
        except IndexError:
            return default

    def sort(self):
        self._container.sort()

    # def sort(self):
    #     tasks = sorted(self._taskdict.values())
    #     for i, task in enumerate(tasks):
    #         self._taskdict[i + 1] = task

    def to_file(self):
        if not self.filename:
            raise AttributeError("TaskList doesn't have a filename!")

        with open(self.filename, "w") as file:
            file.write(self.to_string())
            LOG.info("Wrote to %s", file)

    def to_string(self, print_index: bool = False, skip_tags: bool = False):
        string = ""

        if print_index:
            oom = len(str(len(self._container)))
            string = "\n".join(
                f"{i + 1:>0{oom}}: {task.to_string(skip_tags)}"
                for i, task in enumerate(self)
            )
        else:
            string = "\n".join(
                task.to_string(skip_tags) for i, task in enumerate(self)
            )

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

    def _filter_str(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> List[Task]:
        if not case_sens:
            search = search.lower()

        results = []

        for task in self:
            tgt = getattr(task, target)
            if not case_sens:
                tgt = tgt.lower()

            if (strict and search == tgt) or (not strict and search in tgt):
                results.append(task)

        return results

    def _filter_bool(
        self, search: bool, target: str,
    ) -> List[Task]:

        results = []

        for task in self:
            tgt = getattr(task, target)

            if tgt == search:
                results.append(task)

        return results

    def _filter_iterable(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> List[Task]:
        if not case_sens:
            search = search.lower()

        results = []

        for task in self:
            for item in getattr(task, target):
                if not case_sens:
                    item = item.lower()

                if (strict and search == item) or (
                    not strict and search in item
                ):
                    results.append(task)

        return results

    def _filter_keyword(
        self,
        search: str,
        strict: bool,
        case_sens: bool,
    ) -> List[Task]:
        if not case_sens:
            search = search.lower()

        try:
            search_key, search_value = search.split(":")
            single_value = False
        except ValueError:
            single_value = True

        results = []

        for task in self:
            for key, value in task.keywords.items():
                if not case_sens:
                    key = key.lower()
                    value = value.lower()

                if single_value and strict:
                    if search == key or search == value:
                        results.append(task)

                elif single_value and not strict:
                    if search in key or search in value:
                        results.append(task)

                elif not single_value and strict:
                    if search_key == key and search_value == value:
                        results.append(task)

                elif not single_value and not strict:
                    if search_key in key and search_value in value:
                        results.append(task)

                else:
                    raise RuntimeError("Fundamental error in boolean logic.")

        return results

    def filter_by(
        self,
        search: Union[bool, str],
        target: str,
        strict: bool = False,
        case_sens: bool = False,
    ) -> "TaskList":
        if target in ("context", "project"):
            assert isinstance(search, str)
            results = self._filter_iterable(
                search, target + "s", strict, case_sens
            )

        elif target in ("contexts", "projects"):
            assert isinstance(search, str)
            results = self._filter_iterable(search, target, strict, case_sens)

        elif target in ("msg", "priority"):
            assert isinstance(search, str)
            results = self._filter_str(search, target, strict, case_sens)

        elif target == "complete":
            assert isinstance(search, bool)
            if strict or case_sens:
                raise ValueError(
                    "strict and case-sensitive don't make "
                    "sense for when filtering booleans!"
                )
            results = self._filter_bool(search, target)

        elif target == "keyword":
            assert isinstance(search, str)
            results = self._filter_keyword(search, strict, case_sens)

        # elif target == "date":
        #     pass
        else:
            raise ValueError(f'Unable to filter by "{target}"')

        return type(self)(results, filename=self.filename)


class SolTaskList(TaskList):
    def __init__(
        self, iterable: Iterable = None, filename: Path = None
    ) -> None:
        super().__init__(filename=filename)

        self.headers: List[Task] = []
        self.footers: List[Task] = []

        if iterable:
            self.filename = self.filename or getattr(
                iterable, "filename", None
            )
            for task in iterable:
                self.append(task)

    def append(self, value):
        if value.keywords.get("header"):
            self.headers.append(value)

        elif value.keywords.get("footer"):
            self.footers.append(value)

        else:
            super().append(value)

    def to_file(self):
        if not self.filename:
            raise AttributeError("TaskList doesn't have a filename!")

        headers = "\n".join(task.to_string() for task in self.headers)
        tasklist = self.to_string()
        footers = "\n".join(task.to_string() for task in self.footers)

        with open(self.filename, "w") as file:
            file.write("\n".join((headers, tasklist, footers)))
            LOG.info("Wrote to %s", file)

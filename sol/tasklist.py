import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import Iterable, List

from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(MutableMapping):
    def __init__(self, iterable=None, filename=None):
        self.filename: filename
        self._taskdict = {}
        if iterable:
            for elem in iterable:
                self.append(elem)

    def __str__(self) -> str:
        return self.to_string()

    def __delitem__(self, key):
        self._taskdict.__delitem__(key)

    def __getitem__(self, key):
        return self._taskdict.__getitem__(key)

    def __setitem__(self, key, value):
        self._taskdict.__setitem__(key, value)

    def __len__(self):
        return self._taskdict.__len__()

    def __iter__(self):
        return (self._taskdict[i] for i in sorted(self._taskdict.keys()))

    def append(self, task):
        self._taskdict[(len(self._taskdict) + 1)] = task

    def popright(self):
        return self._taskdict.pop(len(self._taskdict))

    def to_file(self):
        if not self.filename:
            raise AttributeError("TaskList doesn't have a filename!")

        with open(self.filename, "w") as file:
            file.write(self.to_string())

    def to_string(self, print_index: bool = False, skip_tags: bool = False):
        string = ""

        if print_index:
            oom = len(str(len(self._taskdict)))
            string = "\n".join(
                f"{i:>0{oom}}: {self._taskdict[i].to_string(skip_tags)}"
                for i in sorted(self._taskdict.keys())
            )
        else:
            string = "\n".join(
                self._taskdict[i].to_string(skip_tags)
                for i in sorted(self._taskdict.keys())
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

    def _filter_var(
        self, search: str, target: str, strict: bool, case_sens: bool,
    ) -> "TaskList":
        if not case_sens:
            search = search.lower()

        results = TaskList(filename=self.filename)

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

        results = TaskList(filename=self.filename)

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
        self, skey: str, svalue: str, strict: bool, case_sens: bool,
    ) -> "TaskList":
        if not case_sens:
            skey = skey.lower()
            svalue = svalue.lower()

        results = TaskList(filename=self.filename)

        for task in self:
            for key, value in task.keywords.items():
                if not case_sens:
                    key = key.lower()
                    value = value.lower()

                if (strict and skey == key and svalue == value) or (
                    not strict and skey in key and svalue in value
                ):
                    results.append(task)

        return results

    def filter_by(
        self,
        search: str,
        target: str,
        strict: bool = False,
        case_sens: bool = False,
    ) -> "TaskList":
        if target in ("context", "project"):
            results = self._filter_iterable(
                search, target + "s", strict, case_sens
            )
        elif target in ("complete", "msg", "priority"):
            results = self._filter_var(
                search, target + "s", strict, case_sens
            )
        elif target == "keyword":
            key, value = search.split(":")
            results = self._filter_keyword(key, value, strict, case_sens)

        # elif target == "date":
        #     pass
        else:
            raise ValueError(f'Unable to filter by "{target}"')

        return results

    # def order(self, reverse: bool = False) -> "TaskList":
    #     results = TaskList(
    #         sorted(self, reverse=reverse), filename=self.filename
    #     )
    #     return results


class SSCS(TaskList):
    def __init__(
        self, tasklist: TaskList = None, filename: Path = None
    ) -> None:
        super().__init__(filename)

        self.headers: List[Task] = []
        self.footers: List[Task] = []

        if tasklist:
            self.filename = tasklist.filename or self.filename
            for task in tasklist:
                self.append(task)

    def append(self, task):
        index = len(self._taskdict) + 1

        if task.keywords.get("c") == "header":
            self.headers.append(task)

        elif task.keywords.get("c") == "footer":
            self.footers.append(task)

        else:
            self._taskdict[index] = task

    def to_file(self):
        if not self.filename:
            raise AttributeError("TaskList doesn't have a filename!")

        headers = "\n".join(task.to_string() for task in self.headers)
        tasklist = self.to_string()
        footers = "\n".join(task.to_string() for task in self.footers)

        with open(self.filename, "w") as file:
            file.write("\n".join((headers, tasklist, footers)))

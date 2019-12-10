import logging
from collections.abc import MutableSequence
from typing import Any, Iterable

from .task import Task

LOG = logging.getLogger(__name__)


class TaskList(MutableSequence):  # pylint: disable=too-many-ancestors
    def __init__(self, iterable=None, *, tasktype=None):
        self.tasktype = tasktype

        self.tasklist: list = []

        for item in iterable or []:
            self.tasklist.append(item)

    def __str__(self) -> str:
        return "\n".join([str(task) for task in self.tasklist])

    def __repr__(self) -> str:
        return self.tasklist.__repr__()

    def __eq__(self, other) -> bool:
        for task in self.tasklist:
            if task not in other:
                return False

        return True

    def __delitem__(self, key: Any):
        return self.tasklist.__delitem__(key)

    def __getitem__(self, key: Any):
        return self.tasklist.__getitem__(key)

    def __len__(self):
        return self.tasklist.__len__()

    def __setitem__(self, key: Any, value: Any):
        return self.tasklist.__setitem__(key, value)

    def insert(self, index: int, value: Any):
        raise NotImplementedError

    # pylint: disable=unidiomatic-typecheck
    def append(self, value: Any):
        if self.tasktype is None:
            self.tasktype = type(value)

        elif not type(value) == self.tasktype:
            raise TypeError("Not allowed to mix classes in TaskList!")

        self.remove_task(value)
        self.tasklist.append(value)

    # pylint: enable=unidiomatic-typecheck

    # pylint: disable=arguments-differ
    def extend(self, iterable: Iterable[Any]):
        try:
            task = next(iter(iterable))
            if self.tasktype is None:
                self.tasktype = type(task)

            # pylint: disable=unidiomatic-typecheck
            condition = all(
                [type(task) == self.tasktype for task in iterable]
            )
            # pylint: enable=unidiomatic-typecheck

            if not condition:
                raise TypeError("Not allowed to mix classes in TaskList!")

            for task in iterable:
                self.remove_task(task)

            return self.tasklist.extend(iterable)

        except StopIteration:
            return self.tasklist

    # pylint: enable=arguments-differ

    def remove_task(self, task: Task):
        try:
            self.tasklist.remove(task)
            return True
        except ValueError:
            return False

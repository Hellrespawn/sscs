# TODO? Check completed date after created date
import logging
import re
from datetime import datetime
from functools import total_ordering
from string import ascii_uppercase
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

from . import EXTRA_VERBOSE

LOG = logging.getLogger(__name__)


@total_ordering
class Task:
    DEFAULT = SimpleNamespace(
        complete="", priority="", date_created=None, date_completed=None
    )

    def __init__(
        self,
        msg: str,
        complete: str = None,
        priority: str = None,
        date_created: datetime = None,
        date_completed: datetime = None,
    ) -> None:
        self.msg = msg
        self.complete = complete or self.DEFAULT.complete
        self.priority = priority or self.DEFAULT.priority
        self.date_created = date_created or self.DEFAULT.date_created
        self.date_completed = date_completed or self.DEFAULT.date_completed

        if self.date_completed and not self.complete:
            raise ValueError("Only completed task can have completion date!")

        LOG.log(EXTRA_VERBOSE, "Created %r", self)
        if self.contexts:
            LOG.log(EXTRA_VERBOSE, "contexts: %r", self.contexts)
        if self.projects:
            LOG.log(EXTRA_VERBOSE, "projects: %r", self.projects)
        if self.keywords:
            LOG.log(EXTRA_VERBOSE, "keywords: %r", self.keywords)

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        if re.fullmatch(r"[A-Z]?", value) is None:
            raise ValueError(f"{value!r} is not a valid priority! ([A-Z]?)")
        self._priority = value

    @property
    def contexts(self):
        return self.get_tags(self.msg, "@")

    @property
    def projects(self):
        return self.get_tags(self.msg, "+")

    @property
    def keywords(self):
        return self.get_keywords(self.msg)

    def __str__(self):
        return self.to_string()

    def to_string(self, skip_tags: bool = False):
        parts = []

        if self.complete:
            parts.append(self.complete)

        if self.priority:
            parts.append(f"({self.priority})")

        if self.date_completed:
            parts.append(self.date_completed.strftime(r"%Y-%m-%d"))

        if self.date_created:
            parts.append(self.date_created.strftime(r"%Y-%m-%d"))

        msg = self.msg

        if skip_tags:
            for key, value in self.keywords.items():
                msg = msg.replace(f"{key}:{value} ", "")
            msg.strip()

        parts.append(" ".join(msg.split()))

        return " ".join(parts)

    def __repr__(self):
        params = (
            "msg",
            "complete",
            "priority",
            "date_created",
            "date_completed",
        )

        args = ", ".join(
            f"{param}={getattr(self, param)!r}"
            for param in params
            if getattr(self, param) is not None
        )

        return f"{__name__}.Task({args})"

    @classmethod
    def comparison_tuple(cls, task):
        return (
            (task.complete != cls.DEFAULT.complete, task.complete),
            (task.priority == cls.DEFAULT.priority, task.priority),
            (
                task.date_created == cls.DEFAULT.date_created,
                task.date_created,
            ),
            (
                task.date_completed == cls.DEFAULT.date_completed,
                task.date_completed,
            ),
            task.msg,
        )

    def __eq__(self, other):
        return self.comparison_tuple(self) == self.comparison_tuple(other)

    def __lt__(self, other):
        return self.comparison_tuple(self) < self.comparison_tuple(other)

    @classmethod
    def from_string(cls, string):
        complete, msg = cls.get_match(r"(.) (.*)", string)
        if complete and complete != "x":
            raise ValueError(f'Unable to parse checkmark in "{string}"!')

        priority, msg = cls.get_match(r"\((.)\) (.*)", msg)
        if priority and priority not in ascii_uppercase:
            raise ValueError(f'Unable to parse priority in "{string}"!')

        if complete:
            try:
                date_completed, msg = cls.get_date(msg)
            except ValueError:
                raise ValueError(
                    f'Unable to parse completion date in "{string}"!'
                )

        else:
            date_completed = None

        try:
            date_created, msg = cls.get_date(msg)
        except ValueError:
            raise ValueError(
                f'Unable to parse completion date in "{string}"!'
            )

        return cls(msg, complete, priority, date_created, date_completed)

    @staticmethod
    def get_match(expr: str, string: str) -> Tuple[Optional[str], str]:
        match = re.match(expr, string)
        if match:
            return match.group(1), match.group(2)

        return (None, string)

    @classmethod
    def get_date(cls, string: str) -> Tuple[Optional[datetime], str]:
        expr = r"(.{4}-.{2}-.{2}) (.*)"

        date, string = cls.get_match(expr, string)

        if date is not None:
            return datetime.strptime(date, r"%Y-%m-%d"), string

        return None, string

    @staticmethod
    def get_tags(string: str, tag: str) -> List[str]:
        tags = []
        for word in string.split():
            if word.startswith(tag):
                tags.append(word[1:])

        return tags

    @staticmethod
    def get_keywords(string: str) -> Dict[str, str]:
        keywords: Dict[str, str] = {}

        expr = re.compile(r"([^:\s]+):([^:\s]+)")

        for word in string.split():
            match = expr.match(word)
            if match:
                keywords[match.group(1)] = match.group(2)

        return keywords

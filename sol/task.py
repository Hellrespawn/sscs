import logging
import re
from datetime import datetime
from functools import total_ordering
from typing import Dict, List, Optional, Tuple

from . import EXTRA_VERBOSE

LOG = logging.getLogger(__name__)


@total_ordering
class Task:
    def __init__(
        self,
        msg: str,
        complete: str = None,
        priority: str = None,
        date_created: datetime = None,
        date_completed: datetime = None,
    ) -> None:
        self.msg = msg
        self.complete = complete
        self.priority = priority
        self.date_created = date_created
        self.date_completed = date_completed

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
    def contexts(self):
        return self.get_tags(self.msg, "@")

    @property
    def projects(self):
        return self.get_tags(self.msg, "+")

    @property
    def keywords(self):
        return self.get_keywords(self.msg)

    def __str__(self):
        parts = []

        if self.complete:
            parts.append(self.complete)

        if self.priority:
            parts.append(f"({self.priority})")

        if self.date_completed:
            parts.append(self.date_completed.strftime(r"%Y-%m-%d"))

        if self.date_created:
            parts.append(self.date_created.strftime(r"%Y-%m-%d"))

        parts.append(self.msg)

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

    @staticmethod
    def comparison_tuple(task):
        return (
            task.priority,
            task.complete,
            task.date_created,
            task.date_completed,
            task.msg,
        )

    def __eq__(self, other):
        return self.comparison_tuple(self) == self.comparison_tuple(other)

    def __lt__(self, other):
        try:
            return self.comparison_tuple(self) < self.comparison_tuple(other)
        except TypeError:
            return False

    @classmethod
    def from_string(cls, string):
        complete, string = cls.get_match(r"(x) (.*)", string)

        priority, string = cls.get_match(r"\(([A-Z])\) (.*)", string)

        if complete:
            date_completed, string = cls.get_date(string)
        else:
            date_completed = None

        date_created, msg = cls.get_date(string)

        return cls(msg, complete, priority, date_created, date_completed)

    @staticmethod
    def get_match(expr: str, string: str) -> Tuple[Optional[str], str]:
        output: Tuple[Optional[str], str] = (None, string)

        match = re.match(expr, string)
        if match:
            output = match.group(1), match.group(2)

        return output

    @classmethod
    def get_date(cls, string: str) -> Tuple[Optional[datetime], str]:
        expr = r"([0-9]{4}-[0-9]{2}-[0-9]{2}) (.*)"

        date = None
        match, string = cls.get_match(expr, string)

        if match is not None:
            date = datetime.strptime(match, r"%Y-%m-%d")

        return date, string

    @staticmethod
    def get_tags(string: str, tag: str) -> List[str]:
        tags = []
        for word in string.split():
            if word.startswith(tag):
                tags.append(word[1:])

        return tags

    @staticmethod
    def get_keywords(string) -> Dict[str, str]:
        keywords: Dict[str, str] = {}

        expr = re.compile(r"([^:\s]+):([^:\s]+)")

        for word in string.split():
            match = expr.match(word)
            if match:
                keywords[match.group(1)] = match.group(2)

        return keywords

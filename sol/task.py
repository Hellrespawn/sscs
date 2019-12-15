import logging
import re
from datetime import datetime
from enum import Enum
from functools import total_ordering
from typing import Dict, List, Optional, Tuple

from . import EXTRA_VERBOSE

LOG = logging.getLogger(__name__)


@total_ordering
class Task:
    class STATE(Enum):
        TODO = " "
        IDEA = "?"
        INPROGRESS = "/"
        DONE = "x"

    def __init__(
        self,
        msg: str,
        state: STATE = None,
        priority: str = None,
        created: datetime = None,
        completed: datetime = None,
    ) -> None:
        self.msg = msg

        self.state = state or self.STATE.TODO
        self.priority = priority
        self.created = created
        self.completed = completed

        if self.completed and self.state != self.STATE.DONE:
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

        if self.state and self.state != self.STATE.TODO:
            parts.append(self.state.value)

        if self.priority:
            parts.append(f"({self.priority})")

        if self.completed:
            parts.append(self.completed.strftime(r"%Y-%m-%d"))

        if self.created:
            parts.append(self.created.strftime(r"%Y-%m-%d"))

        parts.append(self.msg)

        return " ".join(parts)

    def __repr__(self):
        params = ("msg", "state", "priority", "created", "completed")

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
            task.state,
            task.created,
            task.completed,
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
        state, string = cls.get_state(string)

        priority, string = cls.get_match(r"\(([A-Z])\) (.*)", string)

        if state == cls.STATE.DONE:
            completed, string = cls.get_date(string)
        else:
            completed = None

        created, msg = cls.get_date(string)

        return cls(msg, state, priority, created, completed)

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

    @classmethod
    def get_state(cls, string: str) -> Tuple[Optional["STATE"], str]:
        chars = "".join(s.value for s in cls.STATE)
        expr = r"([" + chars + "]) (.*)"

        state = None
        match, string = cls.get_match(expr, string)

        if match is not None:
            state = cls.STATE(match)

        return state, string

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

# TODO? Check completed date after created date
import re
from datetime import datetime
from functools import total_ordering
from typing import Dict, List, Optional, Tuple

from rich.highlighter import RegexHighlighter
from rich.theme import Theme


class TaskHighlighter(RegexHighlighter):
    """Apply style to [Task]s."""

    base_style = "task."
    highlights = [
        r"(?P<symbols>[(){}\[\]<>:@+-])",
        r"\W(?P<numbers>\d+)",
        r"(?P<quote>'.*?')",
        r"(?P<quote>\".*?\")",
        r"profile:(?P<profile>\w*)",
    ]


TaskTheme = Theme({
    "task.symbols": "bold",
    "task.numbers": "bold blue",
    "task.quote": "#FF8700",
    "task.profile": "bold cyan"
})


@total_ordering
class Task:
    def __init__(
        self,
        msg: str,
        *,
        complete: bool = None,
        priority: str = None,
        date_created: datetime = None,
        date_completed: datetime = None,
    ) -> None:
        self.msg = msg.strip()
        if not self.msg:
            raise ValueError("Task message must not be empty.")

        self.complete = complete or False
        self.priority = priority or ""
        self.date_created = date_created or None
        self.date_completed = date_completed or None

        if self.date_completed and not self.complete:
            raise ValueError("Only completed task can have completion date!")

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

    def __contains__(self, value):
        return value in self.to_string()

    def __eq__(self, other):
        return self.comparison_tuple(self) == self.comparison_tuple(other)

    def __hash__(self):
        return hash(self.comparison_tuple(self))

    def __lt__(self, other):
        return self.comparison_tuple(self) < self.comparison_tuple(other)

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

        return f"Task({args})"

    def __str__(self):
        return self.to_string()

    def contains_term(self, term, sep="/"):
        return any(subterm in self for subterm in term.split(sep))

    def to_string(  # noqa: C901 too complex
        self,
        hide_contexts: bool = False,
        hide_projects: bool = False,
        hide_keywords: bool = False,
    ):
        parts = []

        if self.complete:
            parts.append("x")

        if self.priority:
            parts.append(f"({self.priority})")

        if self.date_completed:
            parts.append(self.date_completed.strftime(r"%Y-%m-%d"))

        if self.date_created:
            parts.append(self.date_created.strftime(r"%Y-%m-%d"))

        msg = self.msg

        if hide_contexts:
            for context in self.contexts:
                msg = msg.replace(f"@{context}", "").replace("  ", " ", 1)

        if hide_projects:
            for project in self.projects:
                msg = msg.replace(f"+{project}", "").replace("  ", " ", 1)

        if hide_keywords:
            for key, value in self.keywords.items():
                msg = msg.replace(f"{key}:{value}", "").replace("  ", " ", 1)

        parts.append(msg)

        return " ".join(parts)

    @classmethod
    def comparison_tuple(cls, task):
        return (
            task.complete is not False,
            task.complete,
            task.priority == "",
            task.priority,
            (
                task.date_created is None,
                task.date_created,
            ),
            (
                task.date_completed is None,
                task.date_completed,
            ),
            task.msg,
        )

    @classmethod
    def from_string(cls, string):
        complete, remainder = cls.get_match_and_remainder(
            r"([xX]) (.*)", string
        )

        priority, remainder = cls.get_match_and_remainder(
            r"\((\S)\) (.*)", remainder
        )

        if complete:
            try:
                date_completed, remainder = cls.get_date(remainder)
            except ValueError:
                raise ValueError(
                    f'Unable to parse completion date in "{string}"!'
                ) from None

        else:
            date_completed = None

        try:
            date_created, remainder = cls.get_date(remainder)
        except ValueError:
            raise ValueError(
                f'Unable to parse completion date in "{string}"!'
            ) from None

        return cls(
            remainder,
            complete=bool(complete),
            priority=priority,
            date_created=date_created,
            date_completed=date_completed,
        )

    @staticmethod
    def get_match_and_remainder(
        expr: str, string: str
    ) -> Tuple[Optional[str], str]:
        match = re.match(expr, string)
        if match:
            return match.group(1), match.group(2)

        return (None, string)

    @classmethod
    def get_date(cls, string: str) -> Tuple[Optional[datetime], str]:
        expr = r"([0-9]{4})-([0-9]{2})-([0-9]{2}) (.*)"

        date, remainder = cls.get_match_and_remainder(expr, string)

        if date is not None:
            return datetime.strptime(date, r"%Y-%m-%d"), remainder

        return None, remainder

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

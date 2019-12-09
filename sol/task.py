from abc import ABC, abstractmethod, abstractclassmethod
import logging
import re
from base64 import b85decode, b85encode
from datetime import datetime
from enum import Enum
from time import time

LOG = logging.getLogger(__name__)


def task_from_string(string):
    class_list = (TimedTask, Task)

    previous = None

    for cls in class_list:
        if previous:
            assert issubclass(previous, cls)

        try:
            task = cls.from_string(string)
            LOG.debug(f"Created task: {task}")
            return task
        except ValueError:
            pass

        previous = cls

    raise FromStringError(string, "Task or subclass of Task!")


class FromStringError(ValueError):
    def __init__(self, string, type_):
        string = f'Unable to parse "{string}" as {type_}!'
        LOG.debug(string)
        super().__init__(string)


class BaseTask(ABC):
    @abstractclassmethod
    def from_string(cls, string):
        pass

    @abstractmethod
    def to_string(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __lt__(self, other):
        pass


class Task(BaseTask):
    """ Datastructure that holds a task.

    Format:
        [$timestamp][$state] $message
        [UFJW-][ ] This is a task
    """

    STATE: Enum = Enum("STATE", "IDEA NOTDONE INPROGRESS DONE")

    TICK_TO_STATE: dict = {
        " ": STATE.NOTDONE,
        "?": STATE.IDEA,
        "/": STATE.INPROGRESS,
        "x": STATE.DONE,
    }

    def __init__(self, msg: str, state: STATE = None) -> None:
        self.msg = Task.filter_string(msg)

        self.state = state or Task.STATE.NOTDONE

        if self.state not in Task.STATE:
            raise TypeError(f'"{self.state}" is not a valid Task state.')

    def __eq__(self, other):
        return self.msg == other.msg and isinstance(other, type(self))

    def __lt__(self, other):
        return (self.state.value, self.msg) < (other.state.value, other.msg)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self):
        return f"Task(msg={self.msg!r}, state={self.state!r})"

    @classmethod
    def from_string(cls, string: str) -> "Task":
        string = cls.filter_string(string)

        # fmt: off
        expr = (
            r"\[(?P<tick>[ ?/xX])\]"  # [$state]
            r"\s*?(?P<msg>.*)"        # $message
        )
        # fmt: on

        match = re.match(expr, string)
        if not match:
            raise FromStringError(string, str(cls))

        state = cls.tick_to_state(match.group("tick").lower())
        msg = cls.filter_string(match.group("msg"))

        return cls(msg, state)

    @staticmethod
    def filter_string(string: str) -> str:
        try:
            index = string.index("#")
            string = string[:index]
        except ValueError:
            pass

        string = string.replace("\n", "")
        string = string.replace("\t", r"%indent%")
        string = string.strip()

        if string.startswith('"') and string.endswith('"'):
            string = string[1:-1]

        return string

    @staticmethod
    def tick_to_state(tick: str) -> "STATE":
        state = Task.TICK_TO_STATE.get(tick.lower(), None)

        if not state:
            raise ValueError(f'Unable to convert "{tick}" to state!')

        return state

    @staticmethod
    def state_to_tick(state: STATE) -> str:
        tick = {v: k for k, v in Task.TICK_TO_STATE.items()}.get(state, None)

        if not tick:
            raise ValueError(f'Unable to convert "{state}" to tick!')

        return tick

    def to_string(self) -> str:
        msg = self.msg.replace('"', r"\"")

        string = f'[{self.state_to_tick(self.state)}] "{msg}"'

        return string


class TimedTask(Task):
    STRFP_FORMAT = "%Y-%m-%d %H:%M"

    def __init__(
        self, msg: str, state: Task.STATE = None, timestamp: int = None
    ) -> None:
        super().__init__(msg, state)

        self.timestamp = timestamp or int(time())

    def __lt__(self, other):
        return (self.state.value, self.timestamp, self.msg) < (
            other.state.value,
            other.timestamp,
            other.msg,
        )

    @classmethod
    def from_string(cls, string: str) -> "TimedTask":
        string = cls.filter_string(string)

        expr = r"\[(?P<timestamp>.+?)\](?P<rest>.*)"

        match = re.match(expr, string)
        if not match:
            raise FromStringError(string, str(cls))

        task = super().from_string(match.group("rest"))

        timestamp = cls.decode_timestamp(match.group("timestamp"))

        return cls(task.msg, task.state, timestamp)

    def to_string(self, parse_timestamp: bool = False) -> str:
        if parse_timestamp:
            return f"[{self.parse_timestamp()}]" + super().to_string()

        return f"[{self.encode_timestamp()}]" + super().to_string()

    def encode_timestamp(self) -> str:
        return b85encode(self.timestamp.to_bytes(4, "big")).decode("utf-8")

    @classmethod
    def decode_timestamp(cls, encoded: str) -> int:
        if len(encoded) == 5:
            return int.from_bytes(b85decode(encoded), "big")

        return int(datetime.strptime(encoded, cls.STRFP_FORMAT).timestamp())

    def parse_timestamp(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime(
            self.STRFP_FORMAT
        )


class CodeTask(Task):
    IDEA_CATEGORIES = ("IDEA", "TODO?")

    def __init__(
        self, msg: str, category: str, line_no: int, state: Task.STATE = None,
    ) -> None:

        self.category = category
        if category in self.IDEA_CATEGORIES and state != Task.STATE.IDEA:
            raise ValueError("CodeTask category does not match state!")
        self.line_no = line_no

        super().__init__(msg, state)

    def __repr__(self):
        return (
            f"CodeTask(msg={self.msg!r}, "
            f"category={self.category!r}, "
            f"line_no={self.line_no!r}, "
            f"state={self.state!r})"
        )

    @classmethod
    def from_string(cls, string):
        task = Task.from_string(string)

        expr = (
            r"(?P<category>.+?)"
            r"@(?P<line_no>[0-9]+)?"
            r":(?P<msg>.*)"
        )

        match = re.match(expr, task.msg)
        if not match:
            raise FromStringError(string, str(cls))

        category = match.group("category")
        line_no = int(match.group("line_no"))
        msg = match.group("msg")

        return cls(msg, category, line_no, task.state)

    def to_string(self):
        msg = self.msg.replace('"', r"\"")

        string = (
            f"[{self.state_to_tick(self.state)}]"
            f' {self.category}@{self.line_no!s}: "{msg}"'
        )

        return string

    @staticmethod
    def filter_comment_chars(string):
        comment_chars = ["#", ";", "//", "/*", "*/"]

        for char in comment_chars:
            if string.startswith(char):
                string = string[len(char):]

            if string.endswith(char):
                string = string[:len(string) - len(char)]

        return string.strip()

    @classmethod
    def from_comment_string(cls, line_no, string):
        string = cls.filter_comment_chars(string)
        category, msg = string.split(maxsplit=1)

        if category in cls.IDEA_CATEGORIES:
            state = cls.STATE.IDEA
        else:
            state = cls.STATE.NOTDONE

        return cls(msg, category, line_no, state)

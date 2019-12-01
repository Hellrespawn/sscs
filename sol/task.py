import logging
import re
from abc import ABC, abstractclassmethod, abstractmethod
from base64 import b85decode, b85encode
from datetime import datetime
from enum import Enum
from time import time

LOG = logging.getLogger(__name__)


class _BaseTask(ABC):
    STATE: Enum = Enum("STATE", "IDEA NOTDONE INPROGRESS DONE")

    TICK_TO_STATE: dict = {
        " ": STATE.NOTDONE,
        "?": STATE.IDEA,
        "/": STATE.INPROGRESS,
        "x": STATE.DONE,
    }

    def __init__(
        self, msg: str, state: STATE = None, timestamp: int = None
    ) -> None:
        self.msg = Task.filter_string(msg)

        self.state = state or Task.STATE.NOTDONE

        if self.state not in Task.STATE:
            raise TypeError(f'"{self.state}" is not a valid Task state.')

        self.timestamp = timestamp or int(time())

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractclassmethod
    def from_string(cls, string: str) -> "_BaseTask":
        pass

    def encode_timestamp(self) -> str:
        return b85encode(self.timestamp.to_bytes(4, "big")).decode("utf-8")

    @staticmethod
    def decode_timestamp(encoded: str) -> int:
        return int.from_bytes(b85decode(encoded), "big")

    @staticmethod
    def parse_timestamp(timestamp: int) -> datetime:
        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def filter_string(string: str) -> str:
        string = string.replace("\n", "")
        string = string.replace("\t", r"%indent%")
        string = string.strip()
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


class Task(_BaseTask):
    def __eq__(self, other):
        return bool(self.msg == other.msg)

    def __str__(self) -> str:
        enc = self.encode_timestamp()
        return f"[{enc}][{self.state_to_tick(self.state)}] {self.msg}"

    @classmethod
    def from_string(cls, string: str) -> "Task":
        string = cls.filter_string(string)

        expr = r"\[(.+?)\]\[([ ?/xX])\]\s+(.*)"

        match = re.match(expr, string)
        if not match:
            raise ValueError(f'Unable to read state from "{string}"!')

        timestamp = cls.decode_timestamp(match.group(1))
        state = cls.tick_to_state(match.group(2))
        msg = cls.filter_string(match.group(3))

        return cls(msg, state, timestamp)


class CodeTask(_BaseTask):
    TYPE = Enum("TYPES", "IDEA TODO? FIXME TODO")

    def __init__(
        self,
        msg: str,
        ttype: TYPE,
        line_no: int,
        state: _BaseTask.STATE = None,
        timestamp: int = None,
    ) -> None:
        if ttype not in self.TYPE:
            raise TypeError("Invalid Task type!")

        if ttype == self.TYPE.IDEA:
            LOG.info(
                'Warning: for compatibility, use "TODO?" instead of "IDEA"'
            )
            ttype = getattr(self.TYPE, "TODO?")

        condition = (ttype == getattr(self.TYPE, "TODO?")) != (
            state == self.STATE.IDEA
        )

        if condition:
            ttype = self.TYPE.TODO

        super().__init__(msg, state, timestamp)

        self.ttype = ttype
        self.line_no = line_no

    def __eq__(self, other):
        return all((super().__eq__(other), self.ttype == other.ttype))

    def __str__(self) -> str:
        enc = self.encode_timestamp()
        # TODO Get digits from settings
        digits = 4

        state = self.state_to_tick(self.state)
        line_no = f"{self.line_no: {digits}d}"

        return f"[{enc}][{state}] {line_no}:{self.ttype.name} {self.msg}"

    @classmethod
    def from_string(cls, string: str) -> "CodeTask":
        task = Task.from_string(string)

        expr = r"([0-9]+):(.+?)\s(.*)"

        match = re.match(expr, task.msg)
        if not match:
            raise ValueError(
                f"Unable to read line number and type " f' from "{task.msg}"!'
            )

        line_no = int(match.group(1))
        ttype = cls.TYPE[match.group(2)]
        msg = match.group(3)

        return cls(msg, ttype, line_no, task.state, task.timestamp)

    @classmethod
    def filter_source_string(cls, string: str) -> str:
        string = string.replace("#", "")
        string = string.replace("//", "")
        string = string.replace("/*", "")
        string = string.replace("*/", "")
        string = cls.filter_string(string)

        return string

    @classmethod
    def from_source_string(cls, string: str, line_no: int) -> "CodeTask":
        string = cls.filter_source_string(string)

        ttype, msg = string.split(maxsplit=1)
        ttype = cls.TYPE[ttype]  # type: ignore

        return CodeTask(msg, ttype, line_no)  # type: ignore

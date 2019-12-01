import re
from abc import ABC, abstractmethod, abstractclassmethod
from enum import Enum
import logging

LOG = logging.getLogger(__name__)


class BaseTask(ABC):
    @abstractmethod
    def __eq__(self, other: "BaseTask") -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractclassmethod
    def from_string(cls, string: str) -> "BaseTask":
        pass


class Task(BaseTask):
    STATE: Enum = Enum("STATE", "NOTDONE IDEA INPROGRESS DONE")

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

    def __eq__(self, other: "Task") -> bool:
        return bool(self.msg == other.msg)

    def __str__(self) -> str:
        return f"[{self.state_to_tick(self.state)}] {self.msg}"

    @classmethod
    def from_string(cls, string: str) -> "Task":
        string = cls.filter_string(string)

        expr = r"\[([ ?/xX])\]\s+(.*)"

        match = re.match(expr, string)
        if not match:
            raise ValueError(f'Unable to read state from "{string}"!')

        msg = cls.filter_string(match.group(2))

        state = cls.tick_to_state(match.group(1))

        return cls(msg, state)

    @staticmethod
    def filter_string(string: str) -> str:
        string = string.replace("\n", "")
        string = string.replace("\t", r"%indent%")
        string = string.strip()
        return string

    @staticmethod
    def tick_to_state(tick: str) -> Enum:
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


class CodeTask(Task):
    TYPE = Enum("TYPES", "FIXME TODO? TODO IDEA")

    def __init__(self, msg, ttype, line_no, state=False) -> None:
        if ttype not in CodeTask.TYPE:
            raise TypeError("Invalid Task type!")

        if ttype == CodeTask.TYPE.IDEA:
            LOG.info(
                'Warning: for compatibility, use "TODO?" instead of "IDEA"'
            )
            ttype = getattr(CodeTask.TYPE, "TODO?")

        super().__init__(msg, state)

        self.ttype = ttype
        self.line_no = line_no

    def __eq__(self, other: "CodeTask") -> bool:
        return any(
            super().__eq__(other),
            self.ttype == other.ttype
        )

    def __str__(self) -> str:
        # TODO Get digits from settings
        digits = 4

        state = self.state_to_tick(self.state)
        line_no = f"{self.line_no: {digits}d}"

        return f"[{state}] {line_no}:{self.ttype.name} {self.msg}"

    @classmethod
    def from_string(cls, string: str) -> "CodeTask":
        task = Task.from_string(string)

        expr = r"([0-9]+):(.+?)\s(.*)"

        match = re.match(expr, task.msg)
        if not match:
            raise ValueError(
                f'Unable to read line number and type '
                f' from "{task.msg}"!'
            )

        line_no = int(match.group(1))
        ttype = cls.TYPE[match.group(2)]
        msg = match.group(3)

        return cls(msg, ttype, line_no, task.state)

    @classmethod
    def filter_source_string(cls, string: str) -> str:
        string = string.replace("#", "")
        string = string.replace("//", "")
        string = string.replace("/*", "")
        string = string.replace("*/", "")
        string = (cls.filter_string(string))

        return string

    @classmethod
    def from_source_string(cls, string: str, line_no: int) -> "CodeTask":
        string = cls.filter_source_string(string)


def main():
    string = "[x] This is a task."
    tsk = Task.from_string(string)
    print(tsk)

    cstring = "[/] 123:FIXME This is a code task"
    ctsk = CodeTask.from_string(cstring)
    print(ctsk)

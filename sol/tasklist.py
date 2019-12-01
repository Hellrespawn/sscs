from abc import ABC, abstractmethod

from .task import CodeTask, Task, _BaseTask


class BaseTaskList(ABC):
    def __init__(self, tclass: _BaseTask) -> None:
        self.tclass = tclass

        self.tasklist = []

    def __str__(self) -> str:
        return "\n".join([str(task) for task in self.tasklist])

    def validate(self, task: Task) -> bool:
        if not isinstance(task, self.tclass):
            raise TypeError(
                f"Invalid class {type(task).__name__}, expected "
                f"{self.tclass.__name__}!"
            )

        return True

    @abstractmethod
    def append(self, task: _BaseTask) -> None:
        pass


class TaskList(BaseTaskList):
    def __init__(self) -> None:
        super().__init__(Task)

    def append(self, task: Task) -> None:
        if self.validate(task):
            try:
                self.tasklist.remove(task)
            except ValueError:
                pass

            self.tasklist.append(task)


class CodeTaskList(BaseTaskList):
    def __init__(self) -> None:
        super().__init__(CodeTask)

    def sort(self):
        self.tasklist.sort(key=lambda t: (t.ttype.value, t.line_no))

    def append(self, task: CodeTask) -> None:
        if self.validate(task):
            try:
                index = self.tasklist.index(task)
                self.tasklist[index].line_no = task.line_no
                self.tasklist[index].state = task.state

            except ValueError:
                self.tasklist.append(task)

            self.sort()


def main():
    # tlist = TaskList()
    # task = Task.from_string("[ ] This is a task.")
    # tlist.append(task)

    # print(str(tlist))

    ctlist = CodeTaskList()
    ctlist.append(CodeTask.from_string("[x] 123:TODO This is a code task."))
    ctlist.append(
        CodeTask.from_string("[x] 234:FIXME This is another code task.")
    )
    ctlist.append(CodeTask.from_string("[?] 156:IDEA This is an idea."))

    print(str(ctlist))

from .task import CodeTask, Task
from .taskdict import TaskDict


def main():
    tstring = "[UF04W][ ] This is a Task."
    ctstring = "[UF04W][ ] 123:FIXME This is a CTask."

    print(Task.from_string(tstring))

    print(CodeTask.from_string(ctstring))

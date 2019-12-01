from .taskdict import TaskDict
from .task import Task


def main():
    taskdict = TaskDict()
    for i in range(2, 0, -1):
        for j in range(4):
            taskdict.append(f"category{i!s}", Task(f"This is task {j!s}."))

    print(taskdict)

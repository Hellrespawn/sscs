from .task import Task, TimedTask
from .tasklist import TaskList


def main():
    tlist = TaskList()
    for i in range(8, 0, -1):
        state = Task.STATE(i % 4 + 1)
        tlist.append(Task(f"Task no. {i}", state))

    tlist2 = TaskList()

    for i in range(8, 0, -1):
        state = Task.STATE(i % 4 + 1)
        task = TimedTask(f"Task no. {i}", state)
        task.timestamp += (8 - i) * 60
        tlist2.append(task)

    print(tlist)
    print()
    print(tlist2)
    print()
    print(TaskList(sorted(tlist)))
    print()
    print(TaskList(sorted(tlist2)))

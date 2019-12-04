from sol import configure_logger

from .taskdict import TaskDict


def main():
    configure_logger(3)
    taskdict = TaskDict.from_file("todo.txt")
    print(taskdict)

    taskdict.to_file("todo.txt")

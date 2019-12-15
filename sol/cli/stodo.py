import logging

import sol

from ..tasklist import TaskList

LOG = logging.getLogger(__name__)


class Stodo:
    def __init__(self) -> None:
        pass


def main():
    sol.configure_logger(999)

    path = sol.LOG_FOLDER.parent

    with open(path / "todo.txt") as file:
        tasklist = TaskList.from_iterable(file)
        print(tasklist)
        print()

        print(TaskList(sorted(tasklist)))
        print()

        print(tasklist.filter.context.strict.case_sens("phone"))
        print()

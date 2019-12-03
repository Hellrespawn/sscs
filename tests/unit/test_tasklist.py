import unittest

from sol.task import Task
from sol.tasklist import TaskList


class TestTaskList(unittest.TestCase):
    @staticmethod
    def get_test_list(lrange, *, order: str = None):
        if order and len(order) != len(lrange):
            raise ValueError(f"Must be {len(lrange)} values")

        if order:
            return TaskList([Task(f"Task {int(i)}") for i in order])

        return TaskList([Task(f"Task {i}") for i in lrange])

    def test_append(self):
        test_list = self.get_test_list(range(1, 8))
        test_list.append(Task("Task 1"))

        comp_list = self.get_test_list(range(1, 8), order="2345671")

        self.assertEqual(
            test_list, comp_list, msg=f"\n{test_list}\n\n{comp_list}"
        )

    def test_extend(self):
        list_a = self.get_test_list(range(1, 8))

        list_b = self.get_test_list(range(3, 6))

        list_c = self.get_test_list(range(1, 8), order="1267345")

        list_a.extend(list_b)

        self.assertEqual(list_a, list_c)

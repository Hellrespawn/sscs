import unittest

from sol.task import _BaseTask, Task, CodeTask


class TestTask(unittest.TestCase):
    def test_bad_state(self):
        with self.assertRaises(TypeError):
            Task("Bad state", "NotAType")

    def test_from_string(self):
        self.assertEqual(
            Task("This is a test"),
            Task.from_string("[ ] This is a test")
        )

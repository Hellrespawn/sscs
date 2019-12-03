import unittest

from sol.task import Task, TimedTask


class TestTask(unittest.TestCase):
    def test_bad_state(self):
        with self.assertRaises(TypeError):
            Task("Bad state", "NotAType")

    def test_from_string(self):
        self.assertEqual(
            Task("This is a test"), Task.from_string("[ ] This is a test")
        )

    def test_to_string(self):
        self.assertEqual(
            Task("This is a test").to_string(), '[ ] "This is a test"'
        )

        self.assertEqual(
            Task("This is\n a test").to_string(), '[ ] "This is a test"'
        )


class TestTimedTask(unittest.TestCase):
    def test_from_string(self):
        task = TimedTask("This is a test")
        enc = task.encode_timestamp()
        self.assertEqual(
            task, TimedTask.from_string(f"[{enc}][ ] This is a test")
        )

    def test_to_string(self):
        task = TimedTask("This is a test")
        enc = task.encode_timestamp()
        self.assertEqual(
            TimedTask("This is a test").to_string(),
            f'[{enc}][ ] "This is a test"',
        )

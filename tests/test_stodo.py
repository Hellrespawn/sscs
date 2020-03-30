import logging
import unittest
from unittest.mock import mock_open, patch

import sol
from logging import configure_logger
from sol.cli.stodo.stodo import STodo
from sol.task import Task

LOG = logging.getLogger()

TODOFILE = """
header:options mode:sol This is a test
(B) c:TODO +sol @cli/stodo_old.py ln:001 More commands: append, prepend, separate check/uncheck, remove, archive
(B) c:TODO +sol @cli/stodo_old.py ln:003 Colorize output
(B) c:TODO +sol @cli/stodo_old.py ln:005 Multiple indices at the same time
(B) c:TODO +sol @cli/stodo_old.py ln:356 Highlight searches
(B) c:TODO +tests @test_stodo.py ln:012 FILE = textwrap.dedent(
(B) c:TODO +tests @test_stodo.py ln:021 FILE)
(C) c:TODO? +sol @cli/sscs.py ln:002 append instead of overwrite flag
(C) c:TODO? +sol @cli/stodo_old.py ln:004 Do validation on options?
(C) c:TODO? +sol @cli/stodo_old.py ln:004 Do validation on options?
(C) c:TODO? +sol @cli/stodo_old.py ln:222 Use dateutil to parse times dynamically
(C) c:TODO? +sol @cli/stodo_old.py ln:262 Delete file if empty?
(C) c:TODO? +sol @cli/stodo_old.py ln:317 Prompt or require flag before appending?
(C) c:TODO? +sol @task.py ln:001 Check completed date after created date
footer:time Generated on 2019-12-29 13:15:08.031440
""".strip()

DONEFILE = """
x (B) c:TODO +sol @cli/stodo_old.py ln:002 Support for done archive
x (B) c:TODO +sol @cli/stodo_old.py ln:245 Implement prompt()
x (C) c:TODO? +sol @cli/sscs.py ln:001 Try opening gitignore
""".strip()


class TestArgs(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_logger(4, sol.LOG_PATH, sol.__name__)
        self.longMessage = True
        self.prefix = "stodo.py"

    def base_arg_test(self, args, todo=None, done=None):
        with patch("sys.argv", [self.prefix] + ["-vvvv"] + args.split()):
            app = STodo()
            todo = todo if todo is not None else TODOFILE.split("\n")
            done = done if done is not None else DONEFILE.split("\n")

            app.todo = [Task.from_string(ln) for ln in todo]
            app.done = [Task.from_string(ln) for ln in done]

            with patch("builtins.open", new_callable=mock_open) as fakefile:
                app.main()
                LOG.debug(fakefile)

    def test_no_args(self):
        self.base_arg_test("")

    def test_unknown_args(self):
        with self.assertRaises(SystemExit):
            self.base_arg_test("unknown")

    def test_append_no_index(self):
        with self.assertRaises(ValueError):
            self.base_arg_test("append")

    def test_append_no_tasks(self):
        with self.assertRaises(ValueError):
            self.base_arg_test("append 1", todo=[])

    def test_append(self):
        self.base_arg_test("append 1 Appending test!")

    def test_prepend_no_index(self):
        with self.assertRaises(ValueError):
            self.base_arg_test("prepend")

    def test_prepend_no_tasks(self):
        with self.assertRaises(ValueError):
            self.base_arg_test("prepend 1", todo=[])

    def test_prepend(self):
        self.base_arg_test("prepend 1 prepending test!")


if __name__ == "__main__":
    unittest.main()

import argparse
import logging
import sys
import unittest

from sol import configure_logger
from sol.cli import cliapp

LOG = logging.getLogger("sol." + __name__)


class TestApp(cliapp.CLIApp):
    def __init__(self, args):
        common_options = argparse.ArgumentParser(add_help=False)

        common_options.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            dest="verbosity",
            help="increase verbosity",
        )

        common_options.add_argument("--force", "-f", action="store_true")

        super().__init__(common_options, args)

    def default(self):
        print("default")

    @cliapp.register_command()
    @cliapp.register_argument("--output", "-o")
    def add(self):
        print("add")

    @cliapp.register_command("print")
    def list(self):
        print("list")


class TestArgs(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_logger(4)
        self.longMessage = True
        self.prefix = sys.argv[0]

    def setUp(self):
        self.settings = None

    def setup_test_values(self, string, *values):
        argnames = ["command", "verbosity", "force"]

        self.settings = TestApp(string.split()).settings
        return dict(zip(argnames, values))

    def arg_test(self, string, *values):
        testdict = self.setup_test_values(string, *values)

        for ctrl_key, ctrl_value in testdict.items():
            self.assertEqual(getattr(self.settings, ctrl_key), ctrl_value)

    def test_no_args(self):
        self.arg_test("", "", 0, False)

    def test_root_args(self):
        self.arg_test("-vv --force", "", 2, True)

    def test_subparser(self):
        self.arg_test("list", "list", 0, False)

    def test_arg_position(self):
        values = ("list", 0, True)
        for args in ("-f list", "list -f"):
            self.arg_test(args, *values)

    def test_argument_from_decorator(self):
        self.setup_test_values("add")
        self.assertTrue(hasattr(self.settings, "output"))


if __name__ == "__main__":
    unittest.main()

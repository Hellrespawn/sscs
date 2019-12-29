import logging
import textwrap
import unittest
from unittest.mock import mock_open, patch

import sol
from loggingextra import configure_logger
from sol.cli.stodo import STodo

LOG = logging.getLogger("sol." + __name__)

TODOFILE = textwrap.dedent(
    """
    (A) This is a +project at @place
    (A) This is also +project at @place
    (B) This is also +project at @place
    """
)


@patch("builtins.open", new_callable=mock_open, read_data=TODOFILE)
class TestArgs(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configure_logger(4, sol.LOG_PATH, sol.__name__)
        self.longMessage = True
        self.prefix = "stodo.py"

    def base_arg_test(self, args):
        with patch("sys.argv", [self.prefix] + args):
            STodo().main()

    def test_no_args(self, mocked_open):
        self.base_arg_test([])

    def test_unknown_args(self, mocked_open):
        with self.assertRaises(SystemExit):
            self.base_arg_test(["unknown"])


if __name__ == "__main__":
    unittest.main()

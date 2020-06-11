from contextlib import ExitStack
from typing import List

import blessed
import sol
from hrshelpers.cli import verbosity_from_args
from hrshelpers.logging import configure_logger


class STodo:
    def __init__(self):
        configure_logger(
            verbosity_from_args(False), sol.LOG_PATH, sol.__name__,
        )

        self.terminal = blessed.Terminal()

        self.text: List[str] = []

        self.header_changed = True

    def run(self):
        term = self.terminal

        ctx_managers = (
            term.hidden_cursor,
            term.raw,
            term.location,
            term.fullscreen,
            term.keypad,
        )

        with ExitStack() as stack:
            for mgr in ctx_managers:
                stack.enter_context(mgr)

            if self.header_changed:
                self.print_header()

            input_key = term.inkey(timeout=1)
            if input_key:
                self.handle_input(input_key)

            else:
                self.recalculate_tasks()

    def print_header(self):
        pass

    def handle_input(self, input_key):
        pass

    def recalculate_tasks(self):
        pass

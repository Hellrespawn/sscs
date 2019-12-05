import argparse
import logging
import re
from pathlib import Path

from sol import configure_logger

from . import task as taskstruct
from .taskdict import TaskDict

LOG = logging.getLogger(__name__)


class CLI:
    def __init__(self):
        self.taskdict = self.get_taskdict()

    @staticmethod
    def get_taskdict():
        paths = (
            Path.home(),
            Path(__file__).parents[0],
            Path(__file__).parents[1],
        )

        filenames = ("todo.txt", ".todo.txt")

        filepaths = [Path(path, name) for path in paths for name in filenames]

        for path in filepaths:
            try:
                taskdict = TaskDict.from_file(path)
                LOG.info(f"Found TaskDict at {path!s}")
                return taskdict

            except FileNotFoundError:
                pass

        LOG.info("Didn't find a TaskDict.")
        return TaskDict()
        # raise FileNotFoundError("No list found!")

    def handle_add(self, args):
        taskstring = " ".join(args.task)

        print(taskstring)

        if re.match(r"\[[ ?/xX]\]", taskstring):
            task = taskstruct.from_string(taskstring)

        else:
            task = taskstruct.Task(taskstring)

        print(f"Adding {task}")

    def handle_check(self, task):
        print(f"Checking {task}")

    def handle_remove(self, task):
        print(f"Removing {task}")

    def handle_print(self, args):
        print(self.taskdict)

    def configure_argparser(self):
        input_commands = ["add", "check", "remove"]
        other_commands = ["print"]
        parser = argparse.ArgumentParser(
            description="Maintains a list of tasks."
        )

        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            help="increase verbosity",
            default=0,
        )

        parser.add_argument(
            "command", nargs="?", default="print",
            choices=sorted(input_commands + other_commands)
        )
        parser.add_argument("task", nargs=argparse.REMAINDER)

        args = parser.parse_args()

        if args.command in input_commands and not args.task:
            parser.error(f"Task is required for {args.command}.")

        args.command = getattr(self, f"handle_{args.command}")

        return args

    def main(self):
        args = self.configure_argparser()
        print(args)


def main():
    configure_logger(3)
    CLI().main()

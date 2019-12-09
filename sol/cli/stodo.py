import argparse
import logging
import re
import sys
from pathlib import Path

from sol import configure_logger

from ..task import task_from_string, Task
from ..taskdict import TaskDict

LOG = logging.getLogger(__name__)


class Stodo:
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
        taskstring = args.input

        print(taskstring)

        if re.match(r"\[[ ?/xX]\]", taskstring):
            task = task_from_string(taskstring)

        else:
            task = Task(taskstring)

        self.taskdict.append(args.category, task)

    def handle_check(self, task):
        print(f"Checking {task}")

    def handle_remove(self, task):
        print(f"Removing {task}")

    @staticmethod
    def handle_print(*args, **kwargs):
        pass

    def configure_argparser(self):
        parser_commands = {
            "task": ("add",),
            "select": ("check", "uncheck", "remove",),
            "no_arg": ("print",)
        }

        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            dest="verbosity",
            help="increase verbosity",
            default=0,
        )

        parser.add_argument(
            "--category",
            "-c",
            help="choose category",
        )

        parser.add_argument(
            "command",
            choices=sum(parser_commands.values(), ()),
            default="print",
            nargs="?"
            )

        parser.add_argument("input", nargs="?")

        args = parser.parse_args()

        if args.command not in parser_commands["no_arg"] and not args.input:
            parser.error(f"{args.command} requires more input!")

        return args

    def main(self):
        args = self.configure_argparser()
        configure_logger(args.verbosity)
        LOG.debug(args)

        try:
            func = getattr(self, f"handle_{args.command}")
        except AttributeError:
            print(f"Unable to parse command: {args.command}")
            sys.exit()

        func(args)

        print(self.taskdict)

        # Write list back


def main():
    Stodo().main()

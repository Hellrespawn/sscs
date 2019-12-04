import click

from pathlib import Path

from sol import configure_logger

from .taskdict import TaskDict


def get_taskdict():
    paths = (
        Path.home(),
        Path(__file__).parents[0],
        Path(__file__).parents[1],
    )

    filenames = (
        "todo.txt",
        ".todo.txt"
    )

    filepaths = [
        Path(path, name) for path in paths for name in filenames
    ]

    for path in filepaths:
        try:
            return TaskDict.from_file(path)
        except FileNotFoundError:
            pass

    raise FileNotFoundError("No list found!")


@click.command()
def main():
    taskdict = get_taskdict()
    print(f"Found at {taskdict.filepath}:\n")
    print(taskdict)

    # taskdict.to_file("todo.txt")

if __name__ == "__main__":
    configure_logger(3)
    main()

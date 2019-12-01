FILENAME = "todo.txt"
FILEPATH = Path(Path(__file__).parents[1], "doc")

LINE_NO_DIGITS = 6

EXT_WHITELIST = ("", ".ebnf", ".md", ".py", ".txt")
FILE_BLACKLIST = (
    lambda file: str(file).startswith("."),
    lambda file: __file__ in str(file),
    lambda file: FILENAME in str(file),
    lambda file: ".egg-info" in str(file),
)


class TaskList:
    def __init__(self):
        self.todo = {}

        self.from_existing_tasklist()

    def __str__(self):
        string = f"# generated on {datetime.now()} #\n"

        for category, tasklist in self.todo.items():
            string += str(category) + ":\n"

            for task in tasklist:
                string += str(task) + "\n"

            string += "\n"

        return string[:-1]

    def append(self, category, task):
        key = str(category)

        if key in self.todo:
            try:
                index = self.todo[key].index(task)
                self.todo[key][index].line_no = task.line_no

            except ValueError:
                self.todo[key].append(task)
        else:
            self.todo[key] = [task]

    def from_dir(self, path=None):
        path = path or Path(__file__).parents[1]

        for filename in path.iterdir():
            if any([func(filename) for func in FILE_BLACKLIST]):
                continue

            if filename.is_dir():
                self.from_dir(filename)

            elif filename.suffix in EXT_WHITELIST:
                self.from_source_file(filename)

    def from_existing_tasklist(self):
        filename = Path(self.filepath, self.filename)

        if filename.exists():
            with open(filename, "r") as file:
                lines = list(file)[1:]

            lines = [line.strip() for line in lines]

            indices = [i for i, line in enumerate(lines) if not line]

            i = 0
            sections = []

            for j in indices:
                if j - i > 1:
                    sections.append(lines[i:j])
                i = j + 1

            sections.append([l for l in lines[i:] if l])

            for section in sections:
                key = section[0].replace(":", "")

                for string in section[1:]:
                    self.append(key, Task.from_tasklist_string(string))

    def from_source_file(self, filename):
        if any([func(filename) for func in FILE_BLACKLIST]):
            raise ValueError("Tried to read blacklisted file!")

        searches = [t.name for t in Task.TYPE]

        with open(filename, "r") as file:
            for i, line in enumerate(file):
                for search in searches:
                    if search in line:
                        try:
                            self.append(
                                filename, Task.from_source_string(line, i + 1)
                            )

                        except SyntaxError:
                            print(
                                f"Unable to parse as Task:\n"
                                f"  {filename!s}:\n"
                                f'    {i + 1}: "{line.strip()}"'
                            )
                        break

    def from_todo_file(self):
        pass

    def to_file(self):
        for key in self.todo:
            self.todo[key].sort(key=lambda t: t.line_no)

        with open(Path(self.filepath, self.filename), "w") as file:
            file.write(str(self))

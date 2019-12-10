# from datetime import datetime
# from enum import Enum
# from pathlib import Path

# from tag_to_filename import ROOT_PATH

# FILENAME = "todo.txt"
# FILEPATH = Path(ROOT_PATH, "doc")

# LINE_NO_DIGITS = 6

# EXT_WHITELIST = ("", ".ebnf", ".md", ".py", ".txt")
# FILE_BLACKLIST = (
#     lambda file: str(file).startswith("."),
#     lambda file: __file__ in str(file),
#     lambda file: FILENAME in str(file),
#     lambda file: ".egg-info" in str(file),
# )
# # TODO Support for done tasks at end
# # Remove line from source when marked done?


# class TaskList:
#     def __init__(self, filename=None, filepath=None):
#         self.filename = filename or FILENAME
#         self.filepath = filepath or FILEPATH

#         self.todo = {}

#         self.from_existing_todo()

#     def __str__(self):
#         string = f"# generated on {datetime.now()} #\n"

#         for filename, tasklist in self.todo.items():
#             string += str(filename) + ":\n"

#             for task in tasklist:
#                 string += str(task) + "\n"

#             string += "\n"

#         return string[:-1]

#     def append(self, filename, task):
#         key = str(filename)

#         if key in self.todo:
#             try:
#                 index = self.todo[key].index(task)
#                 self.todo[key][index].line_no = task.line_no

#             except ValueError:
#                 self.todo[key].append(task)
#         else:
#             self.todo[key] = [task]

#     def from_dir(self, path=None):
#         path = path or Path(__file__).parents[1]

#         for filename in path.iterdir():
#             if any([func(filename) for func in FILE_BLACKLIST]):
#                 continue

#             if filename.is_dir():
#                 self.from_dir(filename)

#             elif filename.suffix in EXT_WHITELIST:
#                 self.from_source_file(filename)

#     def from_existing_todo(self):
#         filename = Path(self.filepath, self.filename)

#         if filename.exists():
#             with open(filename, "r") as file:
#                 lines = list(file)[1:]

#             lines = [line.strip() for line in lines]

#             indices = [i for i, line in enumerate(lines) if not line]

#             i = 0
#             sections = []

#             for j in indices:
#                 if j - i > 1:
#                     sections.append(lines[i:j])
#                 i = j + 1

#             sections.append([l for l in lines[i:] if l])

#             for section in sections:
#                 key = section[0].replace(":", "")

#                 for string in section[1:]:
#                     self.append(key, Task.from_tasklist_string(string))

#     def from_source_file(self, filename):
#         if any([func(filename) for func in FILE_BLACKLIST]):
#             raise ValueError("Tried to read blacklisted file!")

#         searches = [t.name for t in Task.TYPE]

#         with open(filename, "r") as file:
#             for i, line in enumerate(file):
#                 for search in searches:
#                     if search in line:
#                         try:
#                             self.append(
#                                 filename, Task.from_source_string(line, i + 1)
#                             )

#                         except SyntaxError:
#                             print(
#                                 f"Unable to parse as Task:\n"
#                                 f"  {filename!s}:\n"
#                                 f'    {i + 1}: "{line.strip()}"'
#                             )
#                         break

#     def from_todo_file(self):
#         pass

#     def to_file(self):
#         for key in self.todo:
#             self.todo[key].sort(key=lambda t: t.line_no)

#         with open(Path(self.filepath, self.filename), "w") as file:
#             file.write(str(self))

# # FIXME This is a test
# class Task:
#     TYPE = Enum("TYPES", ("FIXME", "TODO?", "TODO", "IDEA"))

#     def __init__(self, msg, ttype, line_no, done=False):
#         if ttype not in Task.TYPE:
#             raise TypeError("Invalid Task type!")

#         if ttype == Task.TYPE.IDEA:
#             print('Warning: for compatibility, use "TODO?" instead of "IDEA"')
#             ttype = getattr(Task.TYPE, "TODO?")

#         self.msg = msg
#         self.ttype = ttype
#         self.line_no = line_no
#         self.done = done

#     def __eq__(self, other):
#         return all(
#             (
#                 self.msg == other.msg,
#                 self.ttype == other.ttype,
#                 self.done == other.done,
#             )
#         )

#     def __str__(self):
#         line_no = f"{self.line_no: {LINE_NO_DIGITS}d}"
#         done = "[x]" if self.done else "[ ]"
#         ttype = self.ttype.name + ": "
#         return f"{line_no}: {done} {ttype} {self.msg}"

#     @staticmethod
#     def filter_string(string):
#         string = string.replace("#", "")
#         string = string.replace(r"/*", "")
#         string = string.replace(r"*/", "")
#         string = string.strip()
#         return string

#     @staticmethod
#     def from_source_string(string, line_no):
#         string = Task.filter_string(string)

#         ttype, msg = string.split(maxsplit=1)

#         ttype = ttype.upper().replace(":", "").strip()
#         msg = msg.strip()

#         try:
#             ttype = Task.TYPE[ttype]
#         except KeyError:
#             raise SyntaxError("Invalid type!")

#         return Task(msg, ttype, line_no)

#     @staticmethod
#     def from_tasklist_string(string):
#         string = Task.filter_string(string)

#         line_no, rest = string.split(maxsplit=1)

#         if rest.startswith("[ ]"):
#             done = False
#         elif rest.startswith("[x]"):
#             done = True
#         else:
#             raise SyntaxError(f"Malformed checkmark: {done}")

#         ttype, msg = rest[3:].strip().split(maxsplit=1)

#         line_no = int(line_no.replace(":", ""))
#         ttype = ttype.upper().replace(":", "").strip()
#         msg = msg.strip()

#         try:
#             ttype = Task.TYPE[ttype]
#         except KeyError:
#             raise SyntaxError(f'Invalid type: "{ttype}"') from None

#         return Task(msg, ttype, line_no, done)


# def main():
#     a = TaskList()
#     a.from_dir()
#     # [print(repr(key)) for key in a.todo.keys()]
#     # import pdb; pdb.set_trace()
#     a.to_file()


# if __name__ == "__main__":
#     main()

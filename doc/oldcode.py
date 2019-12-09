# def from_dir(self, path=None):
#     path = path or Path(__file__).parents[1]

#     for filename in path.iterdir():
#         if any([func(filename) for func in FILE_BLACKLIST]):
#             continue

#         if filename.is_dir():
#             self.from_dir(filename)

#         elif filename.suffix in EXT_WHITELIST:
#             self.from_source_file(filename)


# def from_source_file(self, filename):
#     if any([func(filename) for func in FILE_BLACKLIST]):
#         raise ValueError("Tried to read blacklisted file!")

#     searches = [t.name for t in Task.TYPE]

#     with open(filename, "r") as file:
#         for i, line in enumerate(file):
#             for search in searches:
#                 if search in line:
#                     try:
#                         self.append(
#                             filename, Task.from_source_string(line, i + 1)
#                         )

#                     except SyntaxError:
#                         print(
#                             f"Unable to parse as Task:\n"
#                             f"  {filename!s}:\n"
#                             f'    {i + 1}: "{line.strip()}"'
#                         )
#                     break


# def to_file(self):
#     for key in self.todo:
#         self.todo[key].sort(key=lambda t: t.line_no)

#     with open(Path(self.filepath, self.filename), "w") as file:
#         file.write(str(self))


# class CodeTask(_BaseTask):
#     TYPE = Enum("TYPES", "IDEA TODO? FIXME TODO")

#     def __init__(
#         self,
#         msg: str,
#         ttype: TYPE,
#         line_no: int,
#         state: _BaseTask.STATE = None,
#         timestamp: int = None,
#     ) -> None:
#         if ttype not in self.TYPE:
#             raise TypeError("Invalid Task type!")

#         if ttype == self.TYPE.IDEA:
#             LOG.info(
#                 'Warning: for compatibility, use "TODO?" instead of "IDEA"'
#             )
#             ttype = getattr(self.TYPE, "TODO?")

#         condition = (ttype == getattr(self.TYPE, "TODO?")) != (
#             state == self.STATE.IDEA
#         )

#         if condition:
#             ttype = self.TYPE.TODO

#         super().__init__(msg, state, timestamp)

#         self.ttype = ttype
#         self.line_no = line_no

#     def __eq__(self, other):
#         return all((super().__eq__(other), self.ttype == other.ttype))

#     def __str__(self) -> str:
#         enc = self.encode_timestamp()
#         # TODO Get digits from settings
#         digits = 4

#         state = self.state_to_tick(self.state)
#         line_no = f"{self.line_no: {digits}d}"

#         return f"[{enc}][{state}] {line_no}:{self.ttype.name} {self.msg}"

#     @classmethod
#     def from_string(cls, string: str) -> "CodeTask":
#         task = Task.from_string(string)

#         expr = r"([0-9]+):(.+?)\s(.*)"

#         match = re.match(expr, task.msg)
#         if not match:
#             raise ValueError(
#                 f'Unable to read line number and type from "{task.msg}"!'
#             )

#         line_no = int(match.group(1))
#         ttype = cls.TYPE[match.group(2)]
#         msg = match.group(3)

#         return cls(msg, ttype, line_no, task.state, task.timestamp)

#     @classmethod
#     def filter_source_string(cls, string: str) -> str:
#         string = string.replace("#", "")
#         string = string.replace("//", "")
#         string = string.replace("/*", "")
#         string = string.replace("*/", "")
#         string = cls.filter_string(string)

#         return string

#     @classmethod
#     def from_source_string(cls, string: str, line_no: int) -> "CodeTask":
#         string = cls.filter_source_string(string)

#         ttype, msg = string.split(maxsplit=1)
#         ttype = cls.TYPE[ttype]  # type: ignore

#         return CodeTask(msg, ttype, line_no)  # type: ignore

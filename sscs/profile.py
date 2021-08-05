from os import PathLike
from pathlib import Path
from typing import List


class Profile:
    def __init__(
        self,
        name: str,
        indicator_files: List[PathLike],
        *,
        allowed_extensions: List[str] = None,
        denied_extensions: List[str] = None,
        allowed_files: List[str] = None,
        denied_files: List[str] = None,
        allowed_directories: List[str] = None,
        denied_directories: List[str] = None,
    ):
        self.name = name
        self.indicator_files = indicator_files

        self.allowed_extensions = allowed_extensions or []
        self.denied_extensions = denied_extensions or []
        self.allowed_files = allowed_files or []
        self.denied_files = denied_files or []
        self.allowed_directories = allowed_directories or []
        self.denied_directories = denied_directories or []

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name}, indicator_files={self.indicator_files})"

    def _is_extension_allowed(self, path: Path) -> bool:
        if not path.is_file():
            raise ValueError(f"{path} is not a file!")

        if self.allowed_extensions:
            return bool(path.suffix in self.allowed_extensions)

        return not bool(path.suffix in self.denied_extensions)

    def is_file_allowed(self, path: Path) -> bool:
        if not path.is_file():
            raise ValueError(f"{path} is not a file!")

        filename = str(path.name)

        if filename in self.allowed_files:
            return True

        if filename in self.denied_files:
            return False

        return self._is_extension_allowed(path)

    def is_dir_allowed(self, path: Path) -> bool:
        if not path.is_dir():
            raise ValueError(f"{path} is not a directory!")

        filename = str(path.name)

        if self.allowed_directories:
            return bool(filename in self.allowed_directories)

        return not bool(filename in self.denied_directories)

from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import List


@dataclass
class Profile:
    name: str

    indicator_files: List[PathLike] = field(default_factory=list)

    allowed_extensions: List[str] = field(default_factory=list)
    denied_extensions: List[str] = field(default_factory=list)
    allowed_files: List[str] = field(default_factory=list)
    denied_files: List[str] = field(default_factory=list)
    allowed_directories: List[str] = field(default_factory=list)
    denied_directories: List[str] = field(default_factory=list)

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

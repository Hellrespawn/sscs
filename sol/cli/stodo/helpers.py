from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, List


@dataclass
class Command:
    """Store aliases, name and destination for cli commands."""

    aliases: List[str]
    dest: str = ""
    name: str = field(init=False)

    def __post_init__(self):
        self.name = self.aliases[0]


def modifies(target: str) -> Callable:
    """Set `instance.modified_{todo,done}` to True"""
    valid = ("todo", "done")
    if target not in valid:
        raise ValueError("target must be one of " + ", ".join(valid))

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs) -> Any:
            setattr(self, f"modified_{target}", True)
            return method(self, *args, **kwargs)

        return wrapper

    return decorator


def no_default(method: Callable) -> Callable:
    """Set `instance.run_default` to False."""
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        self.run_default = False
        return method(self, *args, **kwargs)

    return wrapper

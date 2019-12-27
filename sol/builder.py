import logging
from inspect import Parameter, signature
from typing import Callable, List

LOG = logging.getLogger(__name__)


class Attr:
    def __init__(self, name: str, mutually_exclusive: int = 0) -> None:
        self.name = name
        self.mutually_exclusive = self.mutex = mutually_exclusive

        self.value = False

    def __eq__(self, other):
        return (self.name, self.mutex) == (other.name, other.mutex)

    def __repr__(self):
        return f"Attr({self.name!r}, {self.mutex!r}, {self.value!r})"


class Builder:
    def __init__(self, function: Callable):
        self.function = function

        self.attrs: List[Attr] = []

        for name, param in signature(self.function).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                mutex_str = name[-2:]
                if mutex_str.startswith("_") and mutex_str[-1:].isdigit():
                    mutex = int(mutex_str[1])
                    name = name[:-2]
                else:
                    mutex = 0

                self.attrs.append(Attr(name, int(mutex)))

    @property
    def mutex_groups(self):
        groups = {}

        for attr in self.attrs:
            if attr.mutex > 0 and attr.value:
                groups[attr.mutex] = attr.name

        return groups

    def __getattr__(self, search: str) -> "Builder":
        for attr in self.attrs:
            if search == attr.name:
                if attr.mutex in self.mutex_groups:
                    raise ValueError(
                        f'"{search}" is mutually exclusive with '
                        f'"{self.mutex_groups[attr.mutex]}"'
                    )

                attr.value = True
                return self

        raise AttributeError(
            f'"{search}" is not a valid attribute of {type(self)}'
        )

    def __call__(self, *args, **kwargs):
        LOG.debug(
            "Applying %s...", ", ".join(a.name for a in self.attrs if a.value)
        )
        for attr in self.attrs:
            name = attr.name
            if attr.mutex > 0:
                name += f"_{attr.mutex}"

            kwargs[name] = attr.value

        self.reset_attrs()

        out = self.function(*args, **kwargs)
        return out

    def reset_attrs(self):
        for attr in self.attrs:
            attr.value = False

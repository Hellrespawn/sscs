import logging
from inspect import Parameter, signature
from typing import Callable, List

LOG = logging.getLogger(__name__)


class Attr:
    def __init__(self, name: str, mutually_exclusive: int = 0) -> None:
        self.name = name
        self.mutually_exclusive = self.mu_ex = mutually_exclusive

        self.value = False

    def __eq__(self, other):
        return (self.name, self.mu_ex) == (other.name, other.mu_ex)

    def __repr__(self):
        return f"Attr({self.name!r}, {self.mu_ex!r}, {self.value!r})"


class Builder:
    def __init__(self, function: Callable):
        self.function = function

        self.attrs: List[Attr] = []

        for name, param in signature(self.function).parameters.items():
            if param.kind == Parameter.KEYWORD_ONLY:
                mu_ex_str = name[-2:]
                if mu_ex_str.startswith("_") and mu_ex_str[-1:].isdigit():
                    mu_ex = int(mu_ex_str[1])
                    name = name[:-2]
                else:
                    mu_ex = 0

                self.attrs.append(Attr(name, int(mu_ex)))

    @property
    def mu_ex_groups(self):
        groups = {}

        for attr in self.attrs:
            if attr.mu_ex > 0 and attr.value:
                groups[attr.mu_ex] = attr.name

        return groups

    def __getattr__(self, search: str) -> "Builder":
        for attr in self.attrs:
            if search == attr.name:
                if attr.mu_ex in self.mu_ex_groups:
                    raise ValueError(
                        f'"{search}" is mutually exclusive with '
                        f'"{self.mu_ex_groups[attr.mu_ex]}"'
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
            if attr.mu_ex > 0:
                name += f"_{attr.mu_ex}"

            kwargs[name] = attr.value

        self.reset_attrs()

        out = self.function(*args, **kwargs)
        return out

    def reset_attrs(self):
        for attr in self.attrs:
            attr.value = False

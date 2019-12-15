from typing import Callable, List


class Attr:
    def __init__(self, name: str, mutually_exclusive: int = 0) -> None:
        self.name = name
        self.mutually_exclusive = self.mu_ex = mutually_exclusive
        # self.required

    def __eq__(self, other):
        return (self.name, self.mu_ex) == (other.name, other.mu_ex)


class Builder:
    def __init__(self, function: Callable, valid_attrs=List[Attr]):
        # TODO Use inspect to dynamically build list of valid attrs
        self.function = function
        self.valid_attrs = valid_attrs
        self.attrs: List[Attr] = []

    def __getattr__(self, search: str) -> "Builder":
        i = -1
        for valid_attr in self.valid_attrs:
            if search == valid_attr.name:
                i = valid_attr.mu_ex

        if i == -1:
            raise AttributeError(f"{search} is not valid for {type(self)}")

        if i > 0:
            for attr in self.attrs:
                if i == attr.mu_ex:
                    raise ValueError(
                        f"{search} is mutually exclusive with {attr.name}"
                    )

        self.attrs.append(Attr(search, i))
        return self

    def __call__(self, *args, **kwargs):
        for attr in self.valid_attrs:
            if attr not in self.attrs and attr.mu_ex > 0:
                kwargs[attr.name] = False
        kwargs.update({attr.name: True for attr in self.attrs})

        out = self.function(*args, **kwargs)

        return out

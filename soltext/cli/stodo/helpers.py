from collections import namedtuple
from functools import wraps
from typing import Any, Callable

Command = namedtuple("Command", ("aliases", "dest"))

COMMAND_LIST = []

VALID_TARGETS = ("todo", "done")


def register(*aliases):
    def decorator(method):
        COMMAND_LIST.append(Command(aliases, dest=method.__name__))
        COMMAND_LIST.sort()
        return method

    return decorator


def modifies(*targets) -> Callable:
    """Set `instance.modified_{todo,done}` to True"""
    if any(target not in VALID_TARGETS for target in targets):
        raise ValueError("targets must be one of " + ", ".join(VALID_TARGETS))

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(instance, arguments) -> Any:
            for target in targets:
                setattr(instance, f"modified_{target}", True)
            return method(instance, arguments)

        return wrapper

    return decorator


def requires(*targets, num_args=0, arbitrary=False) -> Callable:
    """ Require an amount of arguments. """
    if any(target not in VALID_TARGETS for target in targets):
        raise ValueError("targets must be one of " + ", ".join(VALID_TARGETS))

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(instance, arguments) -> Any:
            for target in targets:
                if not getattr(instance, target):
                    raise ValueError(f"self.{target} is empty!")

            if arbitrary:
                if len(arguments) < num_args:
                    raise ValueError(
                        f'"{method.__name__} requires '
                        f"at least {num_args} arguments!"
                    )
            else:
                if len(arguments) != num_args:
                    raise ValueError(
                        f'"{method.__name__} requires {num_args} arguments!"'
                    )

            return method(instance, arguments)

        return wrapper

    return decorator


def no_default(method: Callable) -> Callable:
    """Set `instance.run_default` to False."""

    @wraps(method)
    def wrapper(instance, *args, **kwargs) -> Any:
        instance.run_default = False
        return method(instance, *args, **kwargs)

    return wrapper

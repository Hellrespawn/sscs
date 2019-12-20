import inspect
import logging
import logging.handlers
from datetime import datetime
from functools import wraps
from pathlib import Path

LOG = logging.getLogger()

VERBOSE = 5

_VERBOSITY_TO_LOG_LEVEL = {
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
    4: VERBOSE,
}


def log_input_output(level):
    def log_input_output_decorator(function):
        sig = inspect.signature(function)
        param = next(iter(sig.parameters))
        if param in ("self", "cls"):
            index = 1
        else:
            index = 0

        params = ", ".join([param for param in sig.parameters])
        name = f"{function.__module__}.{function.__name__}({params})"

        @wraps(function)
        def log_input_output_wrapper(*args, **kwargs):
            if LOG.isEnabledFor(level):
                LOG.log(level, "Entering %s", name)
                if args[index:]:
                    LOG.log(level, "    args = %r", args[index:])

                if kwargs:
                    LOG.log(level, "    kwargs = %r", kwargs)

                out = function(*args, *kwargs)
                LOG.log(level, "    return %r", out)

                return out

            return function(*args, *kwargs)

        return log_input_output_wrapper

    return log_input_output_decorator


def configure_logger(verbosity, logging_path, filename, logging_format):
    """Configures the logger.

    Arguments:
        verbosity {int} -- 0 <= verbosity <= 3

    Keyword Arguments:
        filename {str} -- name of log file (default: {None})
        logformat {str} -- "{"-style format string (default: {None})
    """
    if verbosity < 1:
        # We use getEffectiveLevel() for debug functions, so we must set the
        # level even when not logging, because it defaults to logging.WARNING.
        LOG.setLevel(logging.CRITICAL)
        return

    loglevel = _VERBOSITY_TO_LOG_LEVEL[
        min(verbosity, len(_VERBOSITY_TO_LOG_LEVEL))
    ]

    destination = Path(logging_path, filename + ".log")
    logging_path.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        destination, mode="w", delay=True, backupCount=3
    )
    handler.doRollover()

    handler.setFormatter(logging.Formatter(logging_format, style="{"))

    LOG.addHandler(handler)
    LOG.setLevel(loglevel)
    LOG.log(
        "Log started at %s with level %s",
        datetime.now(),
        logging.getLevelName(loglevel),
    )

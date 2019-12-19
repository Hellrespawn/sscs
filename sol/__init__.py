import logging
import logging.handlers
from datetime import datetime
from functools import wraps
from pathlib import Path

__version__ = "0.0.2"
__version_info__ = tuple(
    int(i) for i in __version__.split(".") if i.isdigit()
)

LOG = logging.getLogger()
LOG.addHandler(logging.NullHandler())

LOG_FOLDER: Path = Path(__file__).parents[1] / "log"

# There is nothing lower than logging.DEBUG (10) in the logging library,
# but we want an extra level to avoid being too verbose when using -vvv.
EXTRA_VERBOSE = 5
logging.addLevelName(EXTRA_VERBOSE, "VERBOSE")

_VERBOSITY_TO_LOG_LEVEL = {
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
    4: EXTRA_VERBOSE,
}

MAX_RECURSION = 4


def log_input_output(level, skip_self=True):
    def log_input_output_decorator(function):
        @wraps(function)
        def log_input_output_wrapper(*args, **kwargs):
            LOG.log(level, function.__module__ + "." + function.__name__)
            if skip_self:
                printargs = args[1:]
            else:
                printargs = args

            if printargs:
                LOG.log(level, "args = %r", printargs)

            if kwargs:
                LOG.log(level, "kwargs = %r", kwargs)

            out = function(*args, *kwargs)
            if out is not None:
                LOG.log(level, "return %r", out)

            return out

        return log_input_output_wrapper

    return log_input_output_decorator


def configure_logger(verbosity: int, log_folder: Path = None) -> None:
    """Configures the logger. """
    if verbosity < 1:
        return

    global LOG_FOLDER  # pylint: disable=global-statement
    LOG_FOLDER = log_folder or LOG_FOLDER

    LOG_FOLDER.mkdir(parents=True, exist_ok=True)

    loglevel = _VERBOSITY_TO_LOG_LEVEL[
        min(verbosity, len(_VERBOSITY_TO_LOG_LEVEL))
    ]

    destination = LOG_FOLDER / (__name__ + ".log")

    handler = logging.handlers.RotatingFileHandler(
        destination, mode="w", delay=True, backupCount=3
    )
    handler.doRollover()

    handler.setFormatter(
        logging.Formatter(
            # "{levelname:.1} [{module}:{funcName}]: {message}", style="{"
            "{levelname:.1} [{name}:{lineno:>04}]: {message}",
            style="{",
        )
    )

    LOG.addHandler(handler)
    LOG.setLevel(loglevel)
    LOG.log(
        loglevel,
        f"Log started at {datetime.now()} with level "
        f"{logging.getLevelName(loglevel)}.",
    )

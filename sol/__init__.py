# TODO Subclasses of TaskList for subclasses of Tasks
# TODO Remember largest line_no for CodeTask, and format based on it.

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

__version__ = "0.0.1"
__version_info__ = tuple(
    int(i) for i in __version__.split(".") if i.isdigit()
)

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


LOG_PATH = Path(Path(__file__).parents[1], "log")

_LOGFORMAT = "{levelname} [{module}:{funcName}]: {message}"
_VERBOSITY_TO_LOG_LEVEL = {
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


def configure_logger(verbosity, filename=None, logformat=None):
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

    loglevel = _VERBOSITY_TO_LOG_LEVEL[min(verbosity, 3)]

    filename = filename or __name__
    destination = Path(LOG_PATH, filename + ".log")
    LOG_PATH.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        destination, mode="w", delay=True, backupCount=3
    )
    handler.doRollover()

    handler.setFormatter(
        logging.Formatter(logformat or _LOGFORMAT, style="{")
    )

    LOG.addHandler(handler)
    LOG.setLevel(loglevel)
    LOG.log(
        loglevel,
        f"Log started at {datetime.now()} with level "
        f"{logging.getLevelName(loglevel)}.",
    )

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

LOG_FOLDER: Path = Path(__file__).parents[1] / "log"

_VERBOSITY_TO_LOG_LEVEL = {
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}

MAX_VERBOSITY = len(_VERBOSITY_TO_LOG_LEVEL)


def configure_logger(verbosity: int, log_folder: Path = None) -> None:
    """Configures the logger. """
    if verbosity < 1:
        # We use getEffectiveLevel() for debug functions, so we must set the
        # level even when not logging, because it defaults to logging.WARNING.
        LOG.setLevel(logging.CRITICAL)
        return

    global LOG_FOLDER
    LOG_FOLDER = log_folder or LOG_FOLDER

    LOG_FOLDER.mkdir(parents=True, exist_ok=True)

    loglevel = _VERBOSITY_TO_LOG_LEVEL[min(verbosity, MAX_VERBOSITY)]

    destination = LOG_FOLDER / (__name__ + ".log")

    handler = logging.handlers.RotatingFileHandler(
        destination, mode="w", delay=True, backupCount=3
    )
    handler.doRollover()

    handler.setFormatter(
        logging.Formatter(
            "{levelname} [{module}:{funcName}]: {message}", style="{"
        )
    )

    LOG.addHandler(handler)
    LOG.setLevel(loglevel)
    LOG.log(
        loglevel,
        f"Log started at {datetime.now()} with level "
        f"{logging.getLevelName(loglevel)}.",
    )

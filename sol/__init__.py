import logging
from pathlib import Path

__version__ = "0.0.2"
__version_info__ = tuple(
    int(i) for i in __version__.split(".") if i.isdigit()
)

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

LOG_FORMAT = "{levelname:.1} [{name}:{lineno:>04}]: {message}"
LOG_PATH = Path(__file__).parents[1] / "log"

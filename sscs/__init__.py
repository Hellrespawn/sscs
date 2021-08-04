import logging
from pathlib import Path

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

LOG_PATH = Path(__file__).parents[1] / "log"

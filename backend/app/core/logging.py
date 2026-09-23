import logging
import os
from logging import Logger

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Configure root once; avoid duplicate handlers under reloaders
if not logging.getLogger().handlers:
    logging.basicConfig(level=_LOG_LEVEL, format=_FMT)

logger: Logger = logging.getLogger("ragops")
logger.setLevel(_LOG_LEVEL)

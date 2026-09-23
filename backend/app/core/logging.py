# backend/app/core/logging.py
import logging
import os
import json
from logging import Logger, LogRecord
from datetime import datetime

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

class JSONFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        # Basic record fields
        payload = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }

        # If exception info present, include it
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Include any extra fields set on the record
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in ("name","msg","args","levelname","levelno",
                         "pathname","filename","module","exc_info",
                         "exc_text","stack_info","lineno","funcName",
                         "created","msecs","relativeCreated","thread",
                         "threadName","processName","process","taskName")
        }
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, ensure_ascii=False)

# Configure root logger once (avoid duplicate handlers under reloaders)
if not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.setLevel(_LOG_LEVEL)
    root.addHandler(handler)

logger: Logger = logging.getLogger("ragops")
logger.setLevel(_LOG_LEVEL)

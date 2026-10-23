"""
Zentrales Logging-Modul.

Konsole (farbig, lesbar) + rotierende JSON-Logdateien.

Verwendung:
    from gmail_bot.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Nachricht", extra={"key": "value"})
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "app.log"
_ERROR_LOG_FILE = _LOG_DIR / "errors.log"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3
_LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

_BUILTIN_ATTRS = frozenset({
    "name", "msg", "args", "created", "relativeCreated",
    "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "filename", "module", "pathname", "levelno", "levelname",
    "processName", "process", "threadName", "thread", "message",
    "msecs", "taskName",
})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "func": record.funcName,
            "line": record.lineno,
            "msg": record.message,
        }
        extras = {k: v for k, v in record.__dict__.items()
                  if k not in _BUILTIN_ATTRS and not k.startswith("_")}
        if extras:
            entry["extra"] = extras
        if record.exc_info and record.exc_info[1]:
            entry["error"] = {
                "type": type(record.exc_info[1]).__name__,
                "msg": str(record.exc_info[1]),
                "tb": traceback.format_exception(*record.exc_info),
            }
        return json.dumps(entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m", "INFO": "\033[32m",
        "WARNING": "\033[33m", "ERROR": "\033[31m", "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        c = self.COLORS.get(record.levelname, "")
        lvl = f"{c}{record.levelname:<8}{self.RESET}"
        line = f"{ts} | {lvl} | {record.name}:{record.funcName}:{record.lineno} | {record.message}"
        extras = {k: v for k, v in record.__dict__.items()
                  if k not in _BUILTIN_ATTRS and not k.startswith("_")}
        if extras:
            line += f" | {', '.join(f'{k}={v!r}' for k, v in extras.items())}"
        if record.exc_info and record.exc_info[1]:
            line += "\n" + "".join(traceback.format_exception(*record.exc_info))
        return line


_initialized = False

def setup_logging() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("gmail_bot")
    root.setLevel(getattr(logging, _LOG_LEVEL, logging.DEBUG))
    root.handlers.clear()

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ConsoleFormatter())
    root.addHandler(ch)

    fh = RotatingFileHandler(_LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JsonFormatter())
    root.addHandler(fh)

    eh = RotatingFileHandler(_ERROR_LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(JsonFormatter())
    root.addHandler(eh)

    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)

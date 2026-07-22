"""Structured JSON logging.

On AWS these lines land in CloudWatch, where they can be queried with Logs
Insights and turned into metric filters/alarms. Locally they just print.
Each event is one JSON line: the event name in "msg", fields alongside.
"""
import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {"ts": time.time(), "level": record.levelname,
                "logger": record.name, "msg": record.getMessage()}
        if hasattr(record, "extra_fields"):
            base.update(record.extra_fields)
        return json.dumps(base)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, msg: str, **fields) -> None:
    logger.info(msg, extra={"extra_fields": fields})
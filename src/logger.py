"""
logger.py — Shared logger for the FinTech Compliance Auditor.

Configures a single named logger that writes every log record to two
destinations simultaneously:
  - Console (stdout) — for live feedback during pipeline execution
  - output/langchain_demo.log — for the persistent audit trail required
    as a project deliverable

All modules import via get_logger(), which is idempotent: calling it
multiple times returns the same logger instance without duplicating handlers.
"""

import logging
import os

LOG_PATH = os.path.join("output", "langchain_demo.log")


def get_logger(name: str = "fintech_auditor") -> logging.Logger:
    """
    Return the shared application logger, creating and configuring it on
    the first call.

    Subsequent calls with the same name return the already-configured
    instance (handlers are not added again), making this safe to call
    at module import time from any file.

    Args:
        name: Logger namespace. Defaults to 'fintech_auditor'.

    Returns:
        A logging.Logger writing at INFO level to both console and file.
    """
    os.makedirs("output", exist_ok=True)

    logger = logging.getLogger(name)

    # Guard against duplicate handlers when the module is imported more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler — writes to output/langchain_demo.log (project deliverable)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler — mirrors output to stdout for live monitoring
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

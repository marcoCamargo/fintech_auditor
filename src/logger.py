"""
logger.py
Configura el sistema de logging que escribe simultáneamente
a consola y al archivo output/langchain_demo.log
"""

import logging
import os

LOG_PATH = os.path.join("output", "langchain_demo.log")


def get_logger(name: str = "fintech_auditor") -> logging.Logger:
    os.makedirs("output", exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler → archivo
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Handler → consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

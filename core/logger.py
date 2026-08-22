"""
COSMOS Rocket Propulsion Platform

Module: core.logger
Author: COSMOS Development Team
Version: 0.1.0

Purpose:
    Centralized logging infrastructure for COSMOS.

Description:
    Provides thread-safe logging with console output,
    rotating file handlers, run identifiers, exception
    logging support, and execution timing utilities.

    This module is intended to be the sole logging
    entry point used throughout COSMOS.
"""

from __future__ import annotations

# Standard Library

import logging
import time
import uuid

from contextlib import AbstractContextManager
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Final


__all__ = (
    "CosmosLoggerConfig",
    "SolverTimer",
    "configure_logging",
    "generate_run_id",
    "get_logger",
)


DEFAULT_LOG_FILE: Final[str] = "cosmos.log"
DEFAULT_LOG_DIRECTORY: Final[str] = "logs"


@dataclass(slots=True, frozen=True)
class CosmosLoggerConfig:
    """
    COSMOS logging configuration.
    """

    log_directory: Path
    log_filename: str = DEFAULT_LOG_FILE
    max_bytes: int = 10_000_000
    backup_count: int = 5
    level: int = logging.INFO


def generate_run_id() -> str:
    """
    Generate a unique COSMOS run identifier.

    Returns
    -------
    str
        Unique run identifier.
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]

    return f"RUN-{timestamp}-{unique}"


class CosmosFormatter(logging.Formatter):
    """
    Standard COSMOS log formatter.
    """

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        return super().format(record)


class SolverTimer(AbstractContextManager["SolverTimer"]):
    """
    Context manager for timing engineering calculations.

    Examples
    --------
    >>> logger = get_logger(__name__)
    >>> with SolverTimer(logger, "choked_flow"):
    ...     pass
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
    ) -> None:
        self._logger = logger
        self._operation_name = operation_name
        self._start_time = 0.0

    def __enter__(self) -> "SolverTimer":
        self._start_time = time.perf_counter()

        self._logger.debug(
            "Starting operation '%s'.",
            self._operation_name,
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        elapsed = time.perf_counter() - self._start_time

        if exc_value is None:
            self._logger.info(
                "Operation '%s' completed in %.6f s.",
                self._operation_name,
                elapsed,
            )
        else:
            self._logger.exception(
                "Operation '%s' failed after %.6f s.",
                self._operation_name,
                elapsed,
            )

        return False


def configure_logging(
    config: CosmosLoggerConfig,
) -> None:
    """
    Configure the global COSMOS logging system.

    Parameters
    ----------
    config : CosmosLoggerConfig
        Logging configuration.
    """

    config.log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(config.level)

    formatter = CosmosFormatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(threadName)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log_path = config.log_directory / config.log_filename

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(
    name: str,
) -> logging.Logger:
    """
    Return a configured logger.

    Parameters
    ----------
    name : str
        Logger name.

    Returns
    -------
    logging.Logger
        Logger instance.
    """
    return logging.getLogger(name)
"""
Unit tests for core.logger.
"""

from __future__ import annotations

# Standard Library

import logging

from pathlib import Path

# COSMOS Core

from core.logger import (
    CosmosLoggerConfig,
    SolverTimer,
    configure_logging,
    generate_run_id,
    get_logger,
)


def test_generate_run_id() -> None:
    """
    Verify run ID creation.
    """
    run_id = generate_run_id()

    assert run_id.startswith("RUN-")


def test_get_logger() -> None:
    """
    Verify logger creation.
    """
    logger = get_logger("test_logger")

    assert isinstance(
        logger,
        logging.Logger,
    )


def test_configure_logging(
    tmp_path: Path,
) -> None:
    """
    Verify log directory creation.
    """
    config = CosmosLoggerConfig(
        log_directory=tmp_path,
    )

    configure_logging(config)

    assert tmp_path.exists()


def test_solver_timer_success(
    caplog,
) -> None:
    """
    Verify successful timing log.
    """
    logger = get_logger("timer_success")

    with caplog.at_level(logging.INFO):
        with SolverTimer(
            logger,
            "test_operation",
        ):
            pass

    assert "completed" in caplog.text


def test_solver_timer_exception(
    caplog,
) -> None:
    """
    Verify exception logging.
    """
    logger = get_logger("timer_failure")

    try:
        with caplog.at_level(logging.ERROR):
            with SolverTimer(
                logger,
                "failure_operation",
            ):
                raise ValueError("boom")

    except ValueError:
        pass

    assert "failed" in caplog.text
########################################################################
#                                                                      #
#                          tests/test_load.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Tests the AI ops load end to end, offline: the fixtures load into a
DuckDB file of the test's own, a second load of the same pins changes
nothing, no text column reaches the warehouse, and `dbt build` passes
every model, contract and test on what was loaded, the reconciliation
of every published figure included.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

# Third-party
import duckdb
import pytest
from kds.args import required
from kds.logs import get_logger

# Local
from pipelines.ai_ops import ai_ops
from pipelines.config import AppSettings
from pipelines.warehouse import load
from support import APPS, PIN, FolderReader, settings_in

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Sets the rows each raw table holds after one load of the fixtures")
COUNTS: Final = {
    "runs": 6,
    "cases": 8,
    "scenarios": 5,
    "retrieval_scores": 45,
    "prices": 11,
}
# log.debug("Sets the count of one raw table, by its name")
COUNT: Final = "select count(*) from raw_ai_ops.{}"
# log.debug("Lists words no raw column's name may hold")
TEXT_WORDS: Final = ("messages", "instructions", "arguments", "answer", "prompt", "passage")


########################################################################
#                                                                      #
#                              Load tests                              #
#                                                                      #
########################################################################
# log.debug("Defines one load of the fixtures")
def _load(settings: AppSettings | None = None) -> None:
    """Loads every fixture app and the fixture price list.

    Args:
        settings: Where the warehouse and dlt's state go. Required.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Builds the source over the fixtures")
    source = ai_ops(
        FolderReader(folder=settings.ai_ops_results), APPS, [PIN], loaded_at=datetime.now(UTC)
    )
    # log.debug("Loads it")
    load(settings, name="ai-ops", dataset=settings.ai_ops_dataset, source=source)


# log.debug("Defines the row counts of the raw tables")
def _counts(path: Path | None = None) -> dict[str, int]:
    """Returns each raw table's row count.

    Args:
        path: The DuckDB file. Required.

    Returns:
        Each table's count, by name.
    """
    # log.debug("Takes the file, which the caller must give")
    path = required(path=path)
    # log.debug("Opens the file to read")
    with duckdb.connect(str(path), read_only=True) as db:
        # log.debug("Counts each table; the names are this file's own")
        counts = {t: db.sql(COUNT.format(t)).fetchall() for t in COUNTS}
    # log.debug("Returns each count")
    return {t: rows[0][0] for t, rows in counts.items()}


# log.debug("Defines a warehouse loaded once, which the tests share")
@pytest.fixture(scope="module")
def loaded(tmp_path_factory: pytest.TempPathFactory) -> AppSettings:
    """Loads the fixtures into a new warehouse; returns its settings.

    Args:
        tmp_path_factory: pytest's maker of temporary folders.

    Returns:
        The settings that point at the warehouse.
    """
    # log.debug("Points the settings at a folder of the module's own")
    settings = settings_in(tmp_path_factory.mktemp("warehouse"))
    # log.debug("Loads the fixtures")
    _load(settings)
    # log.debug("Returns the settings")
    return settings


# log.debug("Defines the test of what one load holds")
def test_one_load_holds_every_fixture_row(loaded: AppSettings) -> None:
    """Seven runs, their cases and scenarios, and the price list.

    Args:
        loaded: The loaded warehouse's settings.
    """
    # log.debug("Checks the counts")
    assert _counts(loaded.warehouse_path) == COUNTS


# log.debug("Defines the test that a second load changes nothing")
def test_loading_the_same_pins_again_changes_nothing(loaded: AppSettings) -> None:
    """Every table merges on its key, so a rerun adds no copies.

    Args:
        loaded: The loaded warehouse's settings.
    """
    # log.debug("Loads the same pins again")
    _load(loaded)
    # log.debug("Checks the counts did not move")
    assert _counts(loaded.warehouse_path) == COUNTS


# log.debug("Defines the test that no text reaches the warehouse")
def test_no_raw_column_holds_prompt_answer_or_tool_text(loaded: AppSettings) -> None:
    """The raw tables keep numbers and names, never what was said.

    Args:
        loaded: The loaded warehouse's settings.
    """
    # log.debug("Lists every raw column")
    with duckdb.connect(str(loaded.warehouse_path), read_only=True) as db:
        # log.debug("Reads the columns of the raw schema")
        columns = [
            name
            for (name,) in db.sql(
                "select column_name from information_schema.columns"
                " where table_schema = 'raw_ai_ops'"
            ).fetchall()
        ]
    # log.debug("Checks none is named for text")
    assert not [c for c in columns if any(word in c for word in TEXT_WORDS)]


# log.debug("Defines the test of the dbt build on the loaded fixtures")
def test_dbt_builds_every_model_and_test_on_the_load(loaded: AppSettings) -> None:
    """Contracts, unit tests and the reconciliation all pass.

    The build runs through the command the DAGs run, in a process of
    its own, as it does in production.

    Args:
        loaded: The loaded warehouse's settings.
    """
    # log.debug("Names the build's own target folder, away from the repository's")
    target = str(loaded.warehouse_path.parent / "target")
    # log.debug("Points the command at the test's warehouse")
    env = os.environ | {"WAREHOUSE_PATH": str(loaded.warehouse_path)}
    # log.debug("Builds every model, seed and test")
    build = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pipelines", "dbt", "build", "--target-path", target],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    # log.debug("Checks the build passed, showing its output when it did not")
    assert build.returncode == 0, build.stdout[-3000:]
    # log.debug("Reads the reconciliation")
    with duckdb.connect(str(loaded.warehouse_path), read_only=True) as db:
        # log.debug("Counts the published figures rebuilt and those that agree")
        rebuilt, agreeing = db.sql(
            "select count(*), count(*) filter (where matches) from ai_ops.fct_run_metrics"
        ).fetchone()  # type: ignore[misc]
    # log.debug("Checks every one agreed, and there were many")
    assert (rebuilt == agreeing, rebuilt > 50) == (True, True)

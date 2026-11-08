########################################################################
#                                                                      #
#                        pipelines/transform.py                        #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Runs dbt over the warehouse the loaders filled, with the settings the
loaders used: dbt's profiles.yml reads the DuckDB path and the
Databricks connection from the environment, which this module sets
from config/config.toml and config/.env. So the warehouse's location
is written once, and `dbt build` and the loaders never disagree.

dbt runs as its own process, from this environment's dbt, so each run
starts clean and its log reads as dbt's own.
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
from collections.abc import Sequence
from pathlib import Path

# Third-party
from kds.args import required
from kds.logs import get_logger, log_event

# Local
from pipelines.config import AppSettings

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                               dbt runs                               #
#                                                                      #
########################################################################
# log.debug("Defines the environment profiles.yml reads")
def dbt_env(settings: AppSettings | None = None) -> dict[str, str]:
    """Returns the variables profiles.yml reads, from the settings.

    Args:
        settings: The warehouse and the Databricks connection.
            Required.

    Returns:
        WAREHOUSE_PATH, and the Databricks variables that are set.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Takes the Databricks token, when there is one")
    token = settings.databricks_token
    # log.debug("Lists every variable profiles.yml can read")
    values = {
        "WAREHOUSE_PATH": str(settings.warehouse_path.resolve()),
        "DATABRICKS_HOST": settings.databricks_host,
        "DATABRICKS_HTTP_PATH": settings.databricks_http_path,
        "DATABRICKS_CATALOG": settings.databricks_catalog,
        "DATABRICKS_TOKEN": token.get_secret_value() if token else None,
    }
    # log.debug("Returns the ones that are set")
    return {k: v for k, v in values.items() if v}


# log.debug("Defines one dbt command")
def run_dbt(settings: AppSettings | None = None, args: Sequence[str] | None = None) -> bool:
    """Runs dbt with the settings' project, target and threads.

    Args:
        settings: The dbt project, target, threads and warehouse.
            Required.
        args: The dbt command and its options, such as ["build"].
            Required.

    Returns:
        True when dbt succeeded.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Takes the command, which the caller must give")
    args = required(args=args)
    # log.debug("Names the project, which also holds profiles.yml")
    project = str(settings.dbt_project)
    # log.debug("Takes this environment's dbt, beside its Python")
    dbt = Path(sys.executable).with_name("dbt")
    # log.debug("Adds the project, the profile's folder, the target and the threads")
    command = [
        str(dbt),
        *args,
        *("--project-dir", project, "--profiles-dir", project),
        *("--target", settings.dbt_target, "--threads", str(settings.dbt_threads)),
    ]
    # log.debug("Runs dbt with the warehouse's variables added to this environment")
    done = subprocess.run(command, env=os.environ | dbt_env(settings), check=False)  # noqa: S603
    # log.debug("Logs the outcome")
    log_event(log, "dbt.done", command=args[0], status=done.returncode)
    # log.debug("Returns whether it succeeded")
    return done.returncode == 0

########################################################################
#                                                                      #
#                        pipelines/warehouse.py                        #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Loads a dlt source into the warehouse the settings name: one DuckDB
file on a laptop and in CI, Databricks in production. The source code
is the same for both; only the destination changes.

dlt's usage telemetry is turned off before any pipeline exists, and its
state is kept under data/generated/, beside the DuckDB file, so a clean
clone starts clean.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from typing import Any, Final

# Third-party
import dlt
from dlt.common.pipeline import LoadInfo
from kds.args import required
from kds.logs import get_logger, log_event

# Local
from pipelines.config import DUCKDB, AppSettings

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
# log.debug("Sets dlt's setting for sending usage data to dltHub")
TELEMETRY: Final = "runtime.dlthub_telemetry"


########################################################################
#                                                                      #
#                               Loading                                #
#                                                                      #
########################################################################
# log.debug("Defines the destination the settings name")
def destination(settings: AppSettings | None = None) -> Any:
    """Returns dlt's DuckDB or Databricks destination.

    Args:
        settings: The destination and where it is. Required.

    Returns:
        The destination, ready for a pipeline.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Returns the DuckDB file, making its folder first")
    if settings.warehouse_destination == DUCKDB:
        # log.debug("Makes the file's folder")
        settings.warehouse_path.parent.mkdir(parents=True, exist_ok=True)
        # log.debug("Returns the DuckDB destination")
        return dlt.destinations.duckdb(str(settings.warehouse_path))
    # log.debug("Takes the token, which the settings checked is set")
    token = required(databricks_token=settings.databricks_token)
    # log.debug("Returns Databricks, through the SQL warehouse at the path")
    return dlt.destinations.databricks(
        credentials={
            "server_hostname": settings.databricks_host,
            "http_path": settings.databricks_http_path,
            "access_token": token.get_secret_value(),
            "catalog": settings.databricks_catalog,
        }
    )


# log.debug("Defines one load of a source into one dataset")
def load(
    settings: AppSettings | None = None,
    *,
    name: str | None = None,
    dataset: str | None = None,
    source: Any = None,
) -> LoadInfo:
    """Runs the source into the dataset and fails if any job failed.

    Args:
        settings: The destination and where dlt keeps its state.
            Required.
        name: The pipeline's name, which names its state. Required.
        dataset: The schema the tables load into. Required.
        source: The dlt source. Required.

    Returns:
        dlt's account of the load: packages, jobs and their tables.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Takes the name, which the caller must give")
    name = required(name=name)
    # log.debug("Takes the dataset, which the caller must give")
    dataset = required(dataset=dataset)
    # log.debug("Takes the source, which the caller must give")
    source = required(source=source)
    # log.debug("Turns dlt's usage telemetry off")
    dlt.config[TELEMETRY] = False
    # log.debug("Builds the pipeline, its state beside the warehouse")
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=destination(settings),
        dataset_name=dataset,
        pipelines_dir=str(settings.warehouse_state),
    )
    # log.debug("Runs the load")
    info = pipeline.run(source)
    # log.debug("Fails the command when any job failed")
    info.raise_on_failed_jobs()
    # log.debug("Logs the load")
    log_event(log, "load.done", pipeline=name, dataset=dataset, packages=len(info.loads_ids))
    # log.debug("Returns the account of it")
    return info

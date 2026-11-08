########################################################################
#                                                                      #
#                          dags/warehouse.py                           #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Builds the warehouse whenever a raw schema changes: first a freshness
check on the raw tables, then `dbt build`, which runs every model,
contract, unit test and data test in dependency order and stops a
model's children when it fails, then the docs site with its lineage.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from typing import Final

# Third-party
from airflow.sdk import DAG
from kds.logs import get_logger

# Local
from defaults import DAG_DEFAULTS, RAW_AI_OPS, RAW_EEOC_STATS, pipelines_task

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
# log.debug("Sets the name of the build's task, and the DAG's tag")
BUILD: Final = "build"

########################################################################
#                                                                      #
#                                 DAG                                  #
#                                                                      #
########################################################################
# log.debug("Defines the build, run by either raw schema's update")
with DAG(
    dag_id="build_warehouse",
    schedule=RAW_AI_OPS | RAW_EEOC_STATS,
    tags=["dbt", BUILD],
    doc_md=__doc__,
    **DAG_DEFAULTS,
):
    # log.debug("Checks the raw tables were loaded recently enough")
    fresh = pipelines_task("freshness", "dbt source freshness")
    # log.debug("Builds and tests every model")
    build = pipelines_task(BUILD, "dbt build")
    # log.debug("Writes the docs site and its lineage graph")
    docs = pipelines_task("docs", "dbt docs generate")
    # log.debug("Runs them in order")
    fresh >> build >> docs

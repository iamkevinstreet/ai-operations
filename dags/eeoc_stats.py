########################################################################
#                                                                      #
#                          dags/eeoc_stats.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Loads the EEOC's national charge receipts by basis once a month. The
EEOC revises the table once a year; a monthly check finds a revision
within weeks, and the file's hash on every row shows when it changed.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
from airflow.sdk import DAG
from kds.logs import get_logger

# Local
from defaults import DAG_DEFAULTS, RAW_EEOC_STATS, pipelines_task

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                                 DAG                                  #
#                                                                      #
########################################################################
# log.debug("Defines the monthly load")
with DAG(
    dag_id="load_eeoc_stats",
    schedule="43 7 3 * *",
    tags=["eeoc", "load"],
    doc_md=__doc__,
    **DAG_DEFAULTS,
):
    # log.debug("Loads the EEOC's receipts table")
    pipelines_task("load_receipts", "load eeoc-stats", outlets=[RAW_EEOC_STATS])

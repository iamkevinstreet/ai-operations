########################################################################
#                                                                      #
#                            dags/ai_ops.py                            #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Loads the AI operations data every day: each app's committed results
at its pinned commit, and the workbench's price list, into raw_ai_ops.
The same pins give the same rows, so a rerun or a retry is harmless.
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
from defaults import DAG_DEFAULTS, RAW_AI_OPS, pipelines_task

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
# log.debug("Defines the daily load")
with DAG(
    dag_id="load_ai_ops",
    schedule="17 6 * * *",
    tags=["ai_ops", "load"],
    doc_md=__doc__,
    **DAG_DEFAULTS,
):
    # log.debug("Loads the apps' results and the price list")
    pipelines_task("load_results", "load ai-ops", outlets=[RAW_AI_OPS])

########################################################################
#                                                                      #
#                           dags/defaults.py                           #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-09

What every DAG shares: retries, a timeout, one run at a time, and the
one command every task runs, `python -m pipelines`, in the project's
own environment. Airflow only schedules and retries: the loaders and
dbt never run inside the scheduler, so the two never share packages,
and the same command runs from a laptop, CI or a hosted Airflow.

The asset names what the load writes, so the warehouse build runs
when the raw schema changes, not on a clock of its own.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

# Third-party
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Asset
from kds.args import required
from kds.logs import get_logger

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
# log.debug("Sets where the project is: the environment's say, else this folder's parent")
REPO: Final = os.environ.get("AI_OPERATIONS_HOME", str(Path(__file__).resolve().parents[1]))
# log.debug("Sets the command every task runs, in the project's locked environment")
PIPELINES: Final = "uv run --no-sync python -m pipelines"
# log.debug("Sets the day the schedules start counting from")
START: Final = datetime(2026, 11, 1, tzinfo=UTC)
# log.debug("Sets what every task inherits: retries with backoff and a time limit")
TASK_DEFAULTS: Final[dict[str, Any]] = {
    "owner": "ai-operations",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
}
# log.debug("Sets what every DAG shares: no backfill and one run at a time")
DAG_DEFAULTS: Final[dict[str, Any]] = {
    "start_date": START,
    "catchup": False,
    "max_active_runs": 1,
    "default_args": TASK_DEFAULTS,
}
# log.debug("Names the raw schema the apps' results load into")
RAW_AI_OPS: Final = Asset(name="raw_ai_ops", group="warehouse")


########################################################################
#                                                                      #
#                              DAG parts                               #
#                                                                      #
########################################################################
# log.debug("Defines a task that runs one pipelines command")
def pipelines_task(
    task_id: str | None = None, args: str | None = None, outlets: list[Asset] | None = None
) -> BashOperator:
    """Returns a task running `python -m pipelines <args>` at the repo.

    Args:
        task_id: The task's name in the DAG. Required.
        args: What follows the command, such as "load ai-ops".
            Required.
        outlets: The assets the task updates, if any.

    Returns:
        The task.
    """
    # log.debug("Takes the task's name, which the caller must give")
    task_id = required(task_id=task_id)
    # log.debug("Takes the command's arguments, which the caller must give")
    args = required(args=args)
    # log.debug("Returns the task, its environment the worker's own")
    return BashOperator(
        task_id=task_id,
        bash_command=f"{PIPELINES} {args}",
        cwd=REPO,
        append_env=True,
        outlets=outlets or [],
    )

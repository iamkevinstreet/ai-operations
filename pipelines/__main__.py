########################################################################
#                                                                      #
#                        pipelines/__main__.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

The one command the Makefile, CI and the Airflow DAGs run:

    python -m pipelines load ai-ops       the apps' results and prices
    python -m pipelines load eeoc-stats   the EEOC's national receipts
    python -m pipelines dbt build         any dbt command, such as build

Every load reads its pins and its destination from config/config.toml,
and dbt gets the same warehouse through profiles.yml's variables.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Final

# Third-party
from kds.args import required
from kds.logs import get_logger, setup_logging

# Local
from pipelines.ai_ops import ai_ops
from pipelines.config import AppSettings, get_app_settings
from pipelines.eeoc_stats import eeoc_stats
from pipelines.github import GitHubReader
from pipelines.transform import run_dbt
from pipelines.warehouse import load

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
# log.debug("Sets the pipeline name of the apps' results")
AI_OPS: Final = "ai-ops"
# log.debug("Sets the pipeline name of the EEOC's statistics")
EEOC_STATS: Final = "eeoc-stats"
# log.debug("Sets the subcommand that runs a load")
LOAD: Final = "load"
# log.debug("Sets what the command does, for its help")
ABOUT: Final = "Load the warehouse's sources, or run dbt over them."


########################################################################
#                                                                      #
#                             The command                              #
#                                                                      #
########################################################################
# log.debug("Defines the load of the apps' results and the price list")
def load_ai_ops(settings: AppSettings | None = None) -> None:
    """Loads every app's results at its pin, and the price list.

    Args:
        settings: The pins, GitHub and the warehouse. Required.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Builds the reader of every app at its pin")
    reader = GitHubReader(settings, pins=settings.ai_ops_apps)
    # log.debug("Builds the source, stamped with this load's time")
    source = ai_ops(
        reader,
        list(settings.ai_ops_apps),
        settings.ai_ops_prices_commits,
        loaded_at=datetime.now(UTC),
    )
    # log.debug("Loads it")
    load(settings, name=AI_OPS, dataset=settings.ai_ops_dataset, source=source)


# log.debug("Defines the load of the EEOC's statistics")
def load_eeoc_stats(settings: AppSettings | None = None) -> None:
    """Loads the EEOC's national charge receipts by basis.

    Args:
        settings: The file's address and the warehouse. Required.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Builds the source, stamped with this load's time")
    source = eeoc_stats(settings, loaded_at=datetime.now(UTC))
    # log.debug("Loads it")
    load(settings, name=EEOC_STATS, dataset=settings.eeoc_stats_dataset, source=source)


# log.debug("Defines the command line")
def main(argv: Sequence[str] | None = None) -> int:
    """Runs one load or one dbt command.

    Args:
        argv: The command's arguments; the process's own when None.

    Returns:
        0 on success; 1 when dbt failed. A failed load raises.
    """
    # log.debug("Lists every load by its name on the command line")
    loads: dict[str, Callable[[AppSettings], None]] = {
        AI_OPS: load_ai_ops,
        EEOC_STATS: load_eeoc_stats,
    }
    # log.debug("Describes the command")
    parser = argparse.ArgumentParser(prog="pipelines", description=ABOUT)
    # log.debug("Adds the two subcommands")
    commands = parser.add_subparsers(dest="command", required=True)
    # log.debug("Adds the load subcommand, by the load's name")
    commands.add_parser(LOAD, help="load one source").add_argument("name", choices=loads)
    # log.debug("Adds the dbt subcommand, passing everything after it through")
    commands.add_parser("dbt", help="run dbt").add_argument("args", nargs=argparse.REMAINDER)
    # log.debug("Parses the command line")
    args = parser.parse_args(argv)
    # log.debug("Reads the settings")
    settings = get_app_settings()
    # log.debug("Starts logging to the configured folder")
    setup_logging(settings)
    # log.debug("Runs a load")
    if args.command == LOAD:
        # log.debug("Runs the named load")
        loads[args.name](settings)
        # log.debug("Reports success")
        return 0
    # log.debug("Runs dbt, failing the command when dbt failed")
    return 0 if run_dbt(settings, args.args) else 1


# log.debug("Runs the command when the module is run as a script")
if __name__ == "__main__":
    # log.debug("Exits with main's status")
    raise SystemExit(main())

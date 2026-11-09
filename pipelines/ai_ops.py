########################################################################
#                                                                      #
#                         pipelines/ai_ops.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-09

The dlt source for AI operations: every run each app committed, its
cases, scores and calls, its trace when it has one, and the price list
the calls were costed at.

Each table merges on its key, so loading the same pins twice changes
nothing, and moving a pin adds only the new runs. Every file is read
once per load, whichever tables it feeds. load_ai_ops runs the source
into the warehouse, as `python -m pipelines load ai-ops`.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from functools import cached_property
from typing import Final

# Third-party
import dlt
from dlt.extract.resource import DltResource
from kds.args import required
from kds.logs import get_logger, log_event
from kds.pipelines import load
from pydantic import BaseModel

# Local
from pipelines.config import SETTINGS, AppSettings
from pipelines.github import GitHubReader, Reader
from pipelines.prices import parse_prices
from pipelines.results import is_trace, kind_of, parse_run
from pipelines.rows import (
    AgentCallRow,
    CaseRow,
    PriceRow,
    RetrievalScoreRow,
    RunRow,
    ScenarioRow,
    ScoreRow,
    SpanRow,
    SummaryRow,
    TagRow,
    ToolCallRow,
)
from pipelines.spans import parse_spans

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the folder every app commits its run files to, from the config")
RESULTS: Final = SETTINGS.ai_ops_results
# log.debug("Takes the repository the price list lives in, from the config")
PRICES_REPO: Final = SETTINGS.ai_ops_prices_repo
# log.debug("Takes the price list's path in that repository, from the config")
PRICES_PATH: Final = SETTINGS.ai_ops_prices_path
# log.debug("Takes the text encoding of every file read, from the config")
ENCODING: Final = SETTINGS.files_encoding

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Sets the pipeline's name, which names its state under data/generated/dlt")
PIPELINE: Final = "ai-ops"
# log.debug("Sets the table every trace's spans go to")
SPANS_TABLE: Final = "spans"
# log.debug("Lists every table of a run: its row model and its key")
RUN_TABLES: Final[dict[str, tuple[type[BaseModel], tuple[str, ...]]]] = {
    "runs": (RunRow, ("app", "run_id")),
    "summaries": (SummaryRow, ("app", "run_id", "metric")),
    "cases": (CaseRow, ("app", "run_id", "case_id")),
    "scores": (ScoreRow, ("app", "run_id", "case_id", "metric")),
    "case_tags": (TagRow, ("app", "run_id", "case_id", "tag")),
    "scenarios": (ScenarioRow, ("app", "run_id", "case_id")),
    "agent_model_calls": (AgentCallRow, ("app", "run_id", "case_id", "step")),
    "agent_tool_calls": (ToolCallRow, ("app", "run_id", "case_id", "seq")),
    "retrieval_scores": (
        RetrievalScoreRow,
        ("app", "run_id", "retrieval_mode", "case_id", "metric"),
    ),
    SPANS_TABLE: (SpanRow, ("app", "run_id", "span_id")),
}
# log.debug("Sets the price list's key: a model's prices as of a date")
PRICE_KEY: Final = ("model", "prices_as_of")
# log.debug("Sets how every table loads: a row replaces the row with its key")
MERGE: Final = "merge"


########################################################################
#                                                                      #
#                            AI ops source                             #
#                                                                      #
########################################################################
# log.debug("Defines every app's files, read and parsed once per load")
class Results:
    """Every row of every app's committed files, by table."""

    # log.debug("Defines the constructor")
    def __init__(
        self,
        reader: Reader | None = None,
        apps: Sequence[str] | None = None,
        *,
        loaded_at: datetime | None = None,
    ) -> None:
        """Keeps what to read; nothing is read until a table is asked.

        Args:
            reader: Lists and reads each app's files at its pin.
                Required.
            apps: The apps to load. Required.
            loaded_at: When this load started. Required.
        """
        # log.debug("Takes the reader, which the caller must give")
        self.reader = required(reader=reader)
        # log.debug("Takes the apps, which the caller must give")
        self.apps = required(apps=apps)
        # log.debug("Takes the load's time, which the caller must give")
        self.loaded_at = required(loaded_at=loaded_at)

    # log.debug("Defines every table's rows, read on first use")
    @cached_property
    def tables(self) -> dict[str, list[BaseModel]]:
        """Returns each table's rows from the apps' run and trace files.

        Returns:
            The rows, by table.
        """
        # log.debug("Starts the tables")
        tables: dict[str, list[BaseModel]] = defaultdict(list)
        # log.debug("Walks every app")
        for app in self.apps:
            # log.debug("Takes the commit the app is pinned to")
            commit = self.reader.commit(app)
            # log.debug("Walks every file of its results folder")
            for file in self.reader.files(app, RESULTS):
                # log.debug("Skips the index, the figures and anything not a run or trace")
                if kind_of(file.path) is None:
                    # log.debug("Moves to the next file")
                    continue
                # log.debug("Reads it once")
                text = self.reader.read(app, file.path).decode(ENCODING)
                # log.debug("Adds a trace file's spans")
                if is_trace(file.path):
                    # log.debug("Parses the spans")
                    tables[SPANS_TABLE] += parse_spans(
                        app, file.path, text, loaded_at=self.loaded_at
                    )
                    # log.debug("Moves to the next file")
                    continue
                # log.debug("Adds a run file's rows, table by table")
                for name, rows in parse_run(
                    app, file, text, commit=commit, loaded_at=self.loaded_at
                ).items():
                    # log.debug("Adds the table's rows")
                    tables[name] += rows
        # log.debug("Logs what was read")
        log_event(log, "ai_ops.read", **{name: len(rows) for name, rows in tables.items()})
        # log.debug("Returns the rows")
        return dict(tables)

    # log.debug("Defines one table's rows")
    def rows(self, table: str | None = None) -> Iterator[BaseModel]:
        """Yields the table's rows.

        Args:
            table: The table's name. Required.

        Yields:
            Each row.
        """
        # log.debug("Takes the table, which the caller must give")
        table = required(table=table)
        # log.debug("Yields its rows, none when no file had any")
        yield from self.tables.get(table, [])


# log.debug("Defines the dlt source")
@dlt.source(name="ai_ops", max_table_nesting=0)
def ai_ops(
    reader: Reader | None = None,
    apps: Sequence[str] | None = None,
    prices: Sequence[str] | None = None,
    *,
    loaded_at: datetime | None = None,
) -> list[DltResource]:
    """Returns one resource per raw table, each merging on its key.

    Args:
        reader: Lists and reads each repository at its pin; it must
            also hold the price list's repository. Required.
        apps: The apps whose results to load. Required.
        prices: The utils commits whose price lists to load. Required.
        loaded_at: When this load started. Required.

    Returns:
        The resources: the run tables and the prices.
    """
    # log.debug("Takes the reader, which the caller must give")
    reader = required(reader=reader)
    # log.debug("Takes the apps, which the caller must give")
    apps = required(apps=apps)
    # log.debug("Takes the price list's commits, which the caller must give")
    prices = required(prices=prices)
    # log.debug("Takes the load's time, which the caller must give")
    loaded_at = required(loaded_at=loaded_at)
    # log.debug("Reads every app's files once, for all the tables")
    results = Results(reader, apps, loaded_at=loaded_at)
    # log.debug("Builds a resource per run table")
    resources = [
        dlt.resource(
            results.rows(name),
            name=name,
            primary_key=key,
            write_disposition=MERGE,
            columns=model,
        )
        for name, (model, key) in RUN_TABLES.items()
    ]
    # log.debug("Adds the price list, one version per commit")
    return [
        *resources,
        dlt.resource(
            _prices(reader, prices, loaded_at),
            name="prices",
            primary_key=PRICE_KEY,
            write_disposition=MERGE,
            columns=PriceRow,
        ),
    ]


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
    load(settings, name=PIPELINE, dataset=settings.ai_ops_dataset, source=source)


# log.debug("Defines the price list's rows")
def _prices(
    reader: Reader | None = None,
    commits: Sequence[str] | None = None,
    loaded_at: datetime | None = None,
) -> Iterator[PriceRow]:
    """Yields every model's prices in every version of the price list.

    Args:
        reader: Reads the utils repository at each commit. Required.
        commits: The utils commits that hold each version. Required.
        loaded_at: When this load started. Required.

    Yields:
        Each model's prices, per version.
    """
    # log.debug("Takes the reader, which the caller must give")
    reader = required(reader=reader)
    # log.debug("Takes the commits, which the caller must give")
    commits = required(commits=commits)
    # log.debug("Takes the load's time, which the caller must give")
    loaded_at = required(loaded_at=loaded_at)
    # log.debug("Walks every version")
    for commit in commits:
        # log.debug("Reads the list at that commit")
        text = reader.read(PRICES_REPO, PRICES_PATH, commit=commit).decode(ENCODING)
        # log.debug("Yields its rows")
        yield from parse_prices(text, commit=commit, loaded_at=loaded_at)

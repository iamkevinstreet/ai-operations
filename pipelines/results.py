########################################################################
#                                                                      #
#                         pipelines/results.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Turns each run file an app commits into rows of the raw tables.

The apps commit three kinds of run file:
- The workbench's format (Grounded Q&A, EEOC): each case's scores, time
  and cost, and the run's summary.
- The intake agent's own: each scenario as scored, and each model and
  tool call its agent made.
- Grounded Q&A's retrieval runs: recall and MRR per question per mode.

The parsing only reshapes: a nested score becomes a row, a true or
false becomes 1 or 0. What the numbers mean is the dbt models' work.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, Final

# Third-party
from kds.args import missing, required
from kds.logs import get_logger
from pydantic import BaseModel

# Local
from pipelines.formats import IntakeRun, KdsRun, RetrievalRun
from pipelines.github import GitFile
from pipelines.rows import (
    AgentCallRow,
    CaseRow,
    RetrievalScoreRow,
    RunFormat,
    RunRow,
    ScenarioRow,
    ScoreRow,
    SummaryRow,
    TagRow,
    ToolCallRow,
)

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
# log.debug("Sets the ending of a run file")
JSON: Final = ".json"
# log.debug("Sets the ending of a committed trace file")
SPANS: Final = ".spans.jsonl"
# log.debug("Sets the kind of a trace file")
TRACE: Final = "trace"
# log.debug("Sets the kind and format, and the name's start, of a retrieval run")
RETRIEVAL: Final = "retrieval"
# log.debug("Sets the kind of an evaluation run file")
RUN: Final = "run"
# log.debug("Sets the table a retrieval run's measures go to")
RETRIEVAL_TABLE: Final = "retrieval_scores"
# log.debug("Lists the files of a results folder that are not runs")
NOT_RUNS: Final = frozenset({"index.json", "figures.json"})
# log.debug("Sets the time stamp every run file's name ends with")
STAMP: Final = re.compile(r"(\d{8}T\d{6}Z)$")
# log.debug("Sets how that time stamp is written")
STAMP_FORMAT: Final = "%Y%m%dT%H%M%SZ"
# log.debug("Sets the key only a workbench run file has")
CASES_KEY: Final = '"results"'
# log.debug("Sets the field that names a scenario or a retrieval question")
ID: Final = "id"
# log.debug("Sets the field that lists a scenario's or a question's tags")
TAGS: Final = "tags"
# log.debug("Sets the field that names a scenario's agent run")
AGENT_RUN: Final = "run_id"
# log.debug("Sets the column every row of a case carries")
CASE_ID: Final = "case_id"
# log.debug("Sets the table a case's or a scenario's tags go to")
TAGS_TABLE: Final = "case_tags"
# log.debug("Types the rows of one file, by the table they go to")
Tables = dict[str, list[BaseModel]]
# log.debug("Types a run file read in its format")
Run = KdsRun | IntakeRun | RetrievalRun


########################################################################
#                                                                      #
#                             Run parsing                              #
#                                                                      #
########################################################################
# log.debug("Defines which kind of file a path is")
def kind_of(path: str | None = None) -> str | None:
    """Returns "spans", "retrieval" or "run", or None for other files.

    Args:
        path: The file's path. Required.

    Returns:
        The kind, or None for the index, the figures and anything not
        JSON.
    """
    # log.debug("Takes the path, which the caller must give")
    path = required(path=path)
    # log.debug("Takes the file's name")
    name = PurePosixPath(path).name
    # log.debug("Returns spans for a trace file")
    if name.endswith(SPANS):
        # log.debug("Returns the trace kind")
        return TRACE
    # log.debug("Returns None for anything but a run file")
    if not name.endswith(JSON) or name in NOT_RUNS:
        # log.debug("Returns no kind")
        return None
    # log.debug("Returns retrieval or run by the name")
    return RETRIEVAL if name.startswith(f"{RETRIEVAL}-") else RUN


# log.debug("Defines whether a path is a run's committed trace")
def is_trace(path: str | None = None) -> bool:
    """Returns True for a .spans.jsonl file.

    Args:
        path: The file's path. Required.

    Returns:
        Whether the file is a trace, one span per line.
    """
    # log.debug("Takes the path, which the caller must give")
    path = required(path=path)
    # log.debug("Returns whether its kind is a trace")
    return kind_of(path) == TRACE


# log.debug("Defines a run's id: its file's name without the endings")
def run_id_of(path: str | None = None) -> str:
    """Returns "live-hybrid-20261107T204014Z" for that run's files.

    Args:
        path: A run file's or a trace file's path. Required.

    Returns:
        The run's id, which its run file and trace file share.
    """
    # log.debug("Takes the path, which the caller must give")
    path = required(path=path)
    # log.debug("Takes the file's name")
    name = PurePosixPath(path).name
    # log.debug("Returns it without the trace or the JSON ending")
    return name.removesuffix(SPANS) if name.endswith(SPANS) else name.removesuffix(JSON)


# log.debug("Defines when a run ran, from its id's time stamp")
def run_at_of(run_id: str | None = None) -> datetime:
    """Returns the UTC time stamp a run's id ends with.

    Args:
        run_id: The run's id. Required.

    Returns:
        The time, in UTC.

    Raises:
        ValueError: When the id has no time stamp.
    """
    # log.debug("Takes the id, which the caller must give")
    run_id = required(run_id=run_id)
    # log.debug("Finds the time stamp")
    found = STAMP.search(run_id)
    # log.debug("Refuses an id without one")
    if not found:
        # log.debug("Raises the missing stamp's error")
        raise ValueError(f"no time stamp in run id {run_id!r}")
    # log.debug("Returns it as a UTC time")
    return datetime.strptime(found.group(1), STAMP_FORMAT).replace(tzinfo=UTC)


# log.debug("Defines the rows of one run file")
def parse_run(
    app: str | None = None,
    file: GitFile | None = None,
    text: str | None = None,
    *,
    commit: str | None = None,
    loaded_at: datetime | None = None,
) -> Tables:
    """Returns the run file's rows, by table, whatever its format.

    Args:
        app: The app the file is from. Required.
        file: The file, with its blob SHA. Required.
        text: Its contents. Required.
        commit: The commit it was read at. Required.
        loaded_at: When this load started. Required.

    Returns:
        The rows for runs, summaries and the format's own tables.
    """
    # log.debug("Takes the app, which the caller must give")
    app = required(app=app)
    # log.debug("Takes the file, which the caller must give")
    file = required(file=file)
    # log.debug("Takes the contents, which the caller must give")
    text = required(text=text)
    # log.debug("Takes the commit, which the caller must give")
    commit = required(commit=commit)
    # log.debug("Takes the load's time, which the caller must give")
    loaded_at = required(loaded_at=loaded_at)
    # log.debug("Names the parts every row shares")
    part: dict[str, Any] = {"app": app, "run_id": run_id_of(file.path), "loaded_at": loaded_at}
    # log.debug("Reads the file in its format, told by its name or the key only it has")
    run: Run = (
        RetrievalRun.model_validate_json(text)
        if kind_of(file.path) == RETRIEVAL
        else KdsRun.model_validate_json(text)
        if CASES_KEY in text
        else IntakeRun.model_validate_json(text)
    )
    # log.debug("Parses the format's own tables and counts its cases")
    tables, cases, run_format = _format_rows(run, part)
    # log.debug("Adds the run's row")
    tables["runs"] = [_run_row(run, part, run_format, source=(file, commit), cases=cases)]
    # log.debug("Adds the numbers its summary published; a retrieval run has none")
    tables["summaries"] = [
        SummaryRow(**part, metric=k, metric_value=v)
        for k, v in _numbers(getattr(run, "summary", {})).items()
    ]
    # log.debug("Returns the rows")
    return tables


# log.debug("Defines the format's own rows")
def _format_rows(
    run: Run | None = None, part: dict[str, Any] | None = None
) -> tuple[Tables, int, RunFormat]:
    """Returns the rows only the run's format has, its count and format.

    Args:
        run: The run file, read in its format. Required.
        part: The app, run and load time every row shares. Required.

    Returns:
        The rows by table, how many cases ran, and the format's name.
    """
    # log.debug("Refuses a missing run; required() cannot keep a union's type")
    if run is None:
        # log.debug("Raises the missing run's error")
        raise missing(run=run)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Parses the run by its format")
    match run:
        case KdsRun():
            # log.debug("Returns the workbench's rows")
            return _kds(run, part), len(run.results), "kds"
        case IntakeRun():
            # log.debug("Returns the intake agent's rows")
            return _intake(run, part), len(run.scenarios), "intake"
        case _:
            # log.debug("Reads each question's measures")
            rows = _retrieval(run, part)
            # log.debug("Returns them, with the questions, the same in every mode")
            return {RETRIEVAL_TABLE: list(rows)}, len({r.case_id for r in rows}), RETRIEVAL


# log.debug("Defines the run's own row")
def _run_row(
    run: Run | None = None,
    part: dict[str, Any] | None = None,
    run_format: RunFormat | None = None,
    *,
    source: tuple[GitFile, str] | None = None,
    cases: int | None = None,
) -> RunRow:
    """Returns the run's row: what ran, when, and read from where.

    Args:
        run: The run file, read in its format. Required.
        part: The app, run and load time every row shares. Required.
        run_format: The file's format. Required.
        source: The file and the commit it was read at. Required.
        cases: How many cases the run has. Required.

    Returns:
        The row. An intake run's times are its first scenario's start
        and its last one's end; a retrieval run has none.
    """
    # log.debug("Refuses a missing run; required() cannot keep a union's type")
    if run is None:
        # log.debug("Raises the missing run's error")
        raise missing(run=run)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Refuses a missing format, for the same reason")
    if run_format is None:
        # log.debug("Raises the missing format's error")
        raise missing(run_format=run_format)
    # log.debug("Takes where it was read from, which the caller must give")
    file, commit = required(source=source)
    # log.debug("Takes the count, which the caller must give")
    cases = required(cases=cases)
    # log.debug("Takes each scenario's agent run, which only an intake file has")
    agents = [t.detail.run for t in run.traces] if isinstance(run, IntakeRun) else []
    # log.debug("Takes the fields a retrieval run lacks, blank for it")
    named = run if not isinstance(run, RetrievalRun) else None
    # log.debug("Takes the times only a workbench run records")
    timed = run if isinstance(run, KdsRun) else None
    # log.debug("Returns the row")
    return RunRow(
        **part,
        run_file=file.path,
        run_format=run_format,
        source_commit=commit,
        source_blob_sha=file.sha,
        run_name=named.name if named else RETRIEVAL,
        model=named.model if named else run.settings.model,  # type: ignore[union-attr]
        provider=named.provider if named else None,
        prices_as_of=named.prices_as_of if named else None,
        run_at=run_at_of(run_id_of(file.path)),
        started_at=timed.started_at
        if timed
        else min((a.started_at for a in agents), default=None),
        finished_at=timed.finished_at
        if timed
        else max((a.finished_at for a in agents), default=None),
        cases=cases,
        failures=timed.failures if timed else None,
    )


# log.debug("Defines the rows of the workbench's run format")
def _kds(run: KdsRun | None = None, part: dict[str, Any] | None = None) -> Tables:
    """Returns each case's row, its numeric scores and its tags.

    Args:
        run: The run file. Required.
        part: The app, run and load time every row shares. Required.

    Returns:
        The rows for cases, scores and tags.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Starts the tables")
    tables: Tables = defaultdict(list)
    # log.debug("Walks every case")
    for case in run.results:
        # log.debug("Names the case's part of every row")
        key = part | {CASE_ID: case.case_id}
        # log.debug("Adds the case's row")
        tables["cases"].append(
            CaseRow(
                **key,
                ok=case.ok,
                error_message=case.error,
                latency_ms=case.latency_ms,
                cost_usd=case.cost_usd,
                model_calls=case.calls,
            )
        )
        # log.debug("Adds a row per numeric score")
        tables["scores"] += [
            ScoreRow(**key, metric=k, metric_value=v) for k, v in _numbers(case.scores).items()
        ]
        # log.debug("Adds a row per tag")
        tables[TAGS_TABLE] += [TagRow(**key, tag=t) for t in case.tags]
    # log.debug("Returns the rows")
    return dict(tables)


# log.debug("Defines the rows of the intake agent's run format")
def _intake(run: IntakeRun | None = None, part: dict[str, Any] | None = None) -> Tables:
    """Returns each scenario, its tags, and its model and tool calls.

    Args:
        run: The run file. Required.
        part: The app, run and load time every row shares. Required.

    Returns:
        The rows for scenarios, tags, agent model calls and tool calls.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Starts the tables")
    tables: Tables = defaultdict(list)
    # log.debug("Walks every scenario as scored")
    for scenario in run.scenarios:
        # log.debug("Names the scenario's part of every row")
        key = part | {CASE_ID: scenario[ID]}
        # log.debug("Takes every field but the ones renamed or listed")
        fields = {k: v for k, v in scenario.items() if k not in {ID, TAGS, AGENT_RUN}}
        # log.debug("Adds the scenario's row, which refuses a field it does not know")
        tables["scenarios"].append(ScenarioRow(**key, **fields, agent_run_id=scenario[AGENT_RUN]))
        # log.debug("Adds a row per tag")
        tables[TAGS_TABLE] += [TagRow(**key, tag=t) for t in scenario.get(TAGS, [])]
    # log.debug("Walks every scenario's recorded calls")
    for trace in run.traces:
        # log.debug("Names the scenario's part of every row")
        key = part | {CASE_ID: trace.id}
        # log.debug("Adds a row per model call")
        tables["agent_model_calls"] += [
            AgentCallRow(
                **key,
                step=c.step,
                input_tokens=c.input_tokens,
                output_tokens=c.output_tokens,
                cost_usd=c.cost_usd,
                latency_ms=c.ms,
                stop_reason=c.stop_reason,
            )
            for c in trace.detail.model_calls
        ]
        # log.debug("Adds a row per tool call, leaving its arguments out")
        tables["agent_tool_calls"] += [
            ToolCallRow(
                **key,
                seq=c.seq,
                step=c.step,
                tool=c.tool,
                ok=c.ok,
                error_message=c.error or None,
                latency_ms=c.ms,
                called_at=c.at,
                result_sha256=c.result_sha256,
            )
            for c in trace.detail.tool_calls
        ]
    # log.debug("Returns the rows")
    return dict(tables)


# log.debug("Defines the rows of a retrieval run")
def _retrieval(
    run: RetrievalRun | None = None, part: dict[str, Any] | None = None
) -> list[RetrievalScoreRow]:
    """Returns each question's measures in each search mode.

    Args:
        run: The run file. Required.
        part: The app, run and load time every row shares. Required.

    Returns:
        One row per mode, question and measure.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Returns a row per mode, question and measure")
    return [
        RetrievalScoreRow(**part, retrieval_mode=mode, case_id=q[ID], metric=k, metric_value=v)
        for mode, questions in run.results.items()
        for q in questions
        for k, v in _numbers({k: v for k, v in q.items() if k not in {ID, TAGS}}).items()
    ]


# log.debug("Defines the numbers of a mapping, true and false as 1 and 0")
def _numbers(values: dict[str, Any] | None = None) -> dict[str, float]:
    """Returns the mapping's numeric values as floats; drops the rest.

    Args:
        values: Scores or a summary. Required.

    Returns:
        Each number by its key; a true or false is 1.0 or 0.0.
    """
    # log.debug("Takes the values, which the caller must give")
    values = required(values=values)
    # log.debug("Keeps numbers and truth values, which are numbers in Python")
    return {k: float(v) for k, v in values.items() if isinstance(v, int | float)}

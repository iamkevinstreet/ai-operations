########################################################################
#                                                                      #
#                          pipelines/rows.py                           #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

The raw tables' contract: one model per table, which dlt also reads
for the tables' columns, so a column that is empty in every row still
exists, and a value of the wrong type fails the load instead of
changing the column.

The rows keep what the marts measure and nothing more. Prompt and
answer text, tool arguments and the values a model read stay in the
apps' files: none of them is needed to count, cost or time a run, and
leaving them out keeps the warehouse free of anything a document said.
Every row carries the app and run it came from, and when it was
loaded; a run row also carries the commit and git blob it was read at.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from datetime import date, datetime
from typing import Final, Literal

# Third-party
from kds.logs import get_logger
from pydantic import BaseModel, ConfigDict

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
# log.debug("Types the three kinds of run file the apps commit")
RunFormat = Literal["kds", "intake", "retrieval"]
# log.debug("Sets every row's model settings: frozen, and no field it does not name")
STRICT: Final = ConfigDict(frozen=True, extra="forbid")


########################################################################
#                                                                      #
#                               Raw rows                               #
#                                                                      #
########################################################################
# log.debug("Defines what every row of a run carries")
class RunPart(BaseModel):
    """The app and run a row came from, and when it was loaded."""

    # log.debug("Freezes the row and refuses any field it does not name")
    model_config = STRICT

    # log.debug("Holds the app the row came from")
    app: str
    # log.debug("Holds the run's id, its file's name without the endings")
    run_id: str
    # log.debug("Holds when the load that wrote the row started")
    loaded_at: datetime


# log.debug("Defines a run file")
class RunRow(RunPart):
    """One run file: what ran, when, on which model, read from where."""

    # log.debug("Holds the run file's path in the app's repository")
    run_file: str
    # log.debug("Holds the file's format: kds, intake or retrieval")
    run_format: RunFormat
    # log.debug("Holds the commit the file was read at")
    source_commit: str
    # log.debug("Holds the git blob SHA of the file's exact contents")
    source_blob_sha: str
    # log.debug("Holds the run's name, such as live-hybrid")
    run_name: str
    # log.debug("Holds the model the run called, or the model priced")
    model: str | None
    # log.debug("Holds the model's provider; fake is the offline stand-in")
    provider: str | None
    # log.debug("Holds the date of the prices the costs used")
    prices_as_of: date | None
    # log.debug("Holds when the run ran, from its id's time stamp")
    run_at: datetime
    # log.debug("Holds when it started")
    started_at: datetime | None
    # log.debug("Holds when it finished")
    finished_at: datetime | None
    # log.debug("Holds how many cases, scenarios or questions it ran")
    cases: int
    # log.debug("Holds how many cases raised, where the format says")
    failures: int | None


# log.debug("Defines a figure from a run's own summary")
class SummaryRow(RunPart):
    """One number the app published in the run's summary."""

    # log.debug("Holds the measure's name")
    metric: str
    # log.debug("Holds the measure's value")
    metric_value: float


# log.debug("Defines a case of the workbench's run format")
class CaseRow(RunPart):
    """One case of a run in the workbench's format."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds whether it ran, or the call succeeded, without an error")
    ok: bool
    # log.debug("Holds the error it raised, if any")
    error_message: str | None
    # log.debug("Holds how long it took, in milliseconds")
    latency_ms: int | None
    # log.debug("Holds what its model calls cost, in USD")
    cost_usd: float | None
    # log.debug("Holds how many model calls it made")
    model_calls: int | None


# log.debug("Defines one score of one case")
class ScoreRow(RunPart):
    """One numeric score of a case; true or false is 1 or 0."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds the measure's name")
    metric: str
    # log.debug("Holds the measure's value")
    metric_value: float


# log.debug("Defines one tag of one case")
class TagRow(RunPart):
    """One tag of one case, such as hard or near_duplicate."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds one tag, such as hard or near_duplicate")
    tag: str


# log.debug("Defines a scenario of the intake agent's run format")
class ScenarioRow(RunPart):
    """One scenario of an intake run, as the app scored it."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds the scenario's title")
    title: str
    # log.debug("Holds its category: conflict, clean, ambiguous or failure")
    category: str
    # log.debug("Holds how the agent's run ended")
    outcome: str | None
    # log.debug("Holds how it should have ended")
    expected_outcome: str | None
    # log.debug("Holds the agent's own verdict")
    agent_recommendation: str | None
    # log.debug("Holds the verdict of the app's own checks")
    checks_recommendation: str | None
    # log.debug("Holds the verdict the approver was shown")
    recommendation: str | None
    # log.debug("Holds the verdict it should have been")
    expected_recommendation: str | None
    # log.debug("Holds how many conflicting records were planted")
    planted: int
    # log.debug("Holds how many of them the findings named")
    found: int
    # log.debug("Holds how many parties the email named")
    parties_expected: int
    # log.debug("Holds how many of them the draft named")
    parties_named: int
    # log.debug("Holds how many warnings the draft carried")
    warnings: int
    # log.debug("Holds how many times the agent tried to open a matter")
    open_attempts: int
    # log.debug("Holds whether a matter opened without approval")
    opened_without_approval: bool
    # log.debug("Holds whether a planted failure was handled, where planted")
    handled: bool | None
    # log.debug("Holds how long the scenario took, in seconds")
    seconds: float
    # log.debug("Holds what its model calls cost, in USD")
    cost_usd: float | None
    # log.debug("Holds the tokens the model read")
    input_tokens: int | None
    # log.debug("Holds the tokens the model wrote")
    output_tokens: int | None
    # log.debug("Holds the agent's steps, one model call each")
    steps: int
    # log.debug("Holds how many tool calls the agent made")
    tool_calls: int
    # log.debug("Holds the agent run's own id")
    agent_run_id: str | None


# log.debug("Defines one model call the intake agent recorded")
class AgentCallRow(RunPart):
    """One model call of an intake scenario, from the run file."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds the agent's step")
    step: int
    # log.debug("Holds the tokens the model read")
    input_tokens: int
    # log.debug("Holds the tokens the model wrote")
    output_tokens: int
    # log.debug("Holds what its model calls cost, in USD")
    cost_usd: float | None
    # log.debug("Holds how long it took, in milliseconds")
    latency_ms: int
    # log.debug("Holds why the model stopped")
    stop_reason: str | None


# log.debug("Defines one tool call the intake agent recorded")
class ToolCallRow(RunPart):
    """One tool call of an intake scenario; its arguments stay out."""

    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds the call's place in the scenario's calls")
    seq: int
    # log.debug("Holds the agent's step")
    step: int
    # log.debug("Holds the tool's name")
    tool: str
    # log.debug("Holds whether it ran, or the call succeeded, without an error")
    ok: bool
    # log.debug("Holds the error it raised, if any")
    error_message: str | None
    # log.debug("Holds how long it took, in milliseconds")
    latency_ms: int
    # log.debug("Holds when the tool was called")
    called_at: datetime
    # log.debug("Holds the SHA-256 of the tool's result, not the result")
    result_sha256: str | None


# log.debug("Defines one span of a run's committed trace")
class SpanRow(RunPart):
    """One OpenTelemetry span, with the GenAI attributes it carried."""

    # log.debug("Holds the trace's id")
    trace_id: str
    # log.debug("Holds the span's id")
    span_id: str
    # log.debug("Holds the parent span's id; a trace's root has none")
    parent_id: str | None
    # log.debug("Holds the span's name, such as chat claude-sonnet-5-5")
    span_name: str
    # log.debug("Holds its kind: CLIENT, INTERNAL or SERVER")
    span_kind: str
    # log.debug("Holds when it started")
    started_at: datetime
    # log.debug("Holds when it ended")
    ended_at: datetime
    # log.debug("Holds how long it took, in milliseconds")
    duration_ms: float
    # log.debug("Holds its status: UNSET, OK or ERROR")
    status_code: str
    # log.debug("Holds the service that wrote it")
    service_name: str | None
    # log.debug("Holds that service's version")
    service_version: str | None
    # log.debug("Holds the GenAI operation: chat, retrieval, execute_tool")
    operation: str | None
    # log.debug("Holds the model's provider; fake is the offline stand-in")
    provider: str | None
    # log.debug("Holds the model the call asked for")
    request_model: str | None
    # log.debug("Holds the model that answered")
    response_model: str | None
    # log.debug("Holds the tokens the model read")
    input_tokens: int | None
    # log.debug("Holds the tokens the model wrote")
    output_tokens: int | None
    # log.debug("Holds what its model calls cost, in USD")
    cost_usd: float | None
    # log.debug("Holds why the model stopped")
    finish_reason: str | None
    # log.debug("Holds the error's type, never its message")
    error_type: str | None
    # log.debug("Holds the tool a tool call ran")
    tool_name: str | None
    # log.debug("Holds Langfuse's type for it, such as guardrail")
    observation_type: str | None
    # log.debug("Holds the case an eval span scored; other spans have none")
    eval_case: str | None


# log.debug("Defines one retrieval score of one question in one mode")
class RetrievalScoreRow(RunPart):
    """One retrieval measure of one question under one search mode."""

    # log.debug("Holds the search mode: keyword, semantic or hybrid")
    retrieval_mode: str
    # log.debug("Holds the case, scenario or question's id")
    case_id: str
    # log.debug("Holds the measure's name")
    metric: str
    # log.debug("Holds the measure's value")
    metric_value: float


# log.debug("Defines one model's prices in one version of the price list")
class PriceRow(BaseModel):
    """One model's list prices, per million tokens, as of a date."""

    # log.debug("Freezes the row and refuses any field it does not name")
    model_config = STRICT

    # log.debug("Holds the model the run called, or the model priced")
    model: str
    # log.debug("Holds USD per million input tokens")
    input_per_mtok: float
    # log.debug("Holds USD per million output tokens")
    output_per_mtok: float
    # log.debug("Holds the date of the prices the costs used")
    prices_as_of: date
    # log.debug("Holds the commit the file was read at")
    source_commit: str
    # log.debug("Holds when the load that wrote the row started")
    loaded_at: datetime


# log.debug("Defines one count of the EEOC's national charge receipts")
class ReceiptRow(BaseModel):
    """Charges the EEOC received in one fiscal year citing one basis."""

    # log.debug("Freezes the row and refuses any field it does not name")
    model_config = STRICT

    # log.debug("Holds the EEOC's name for the table, E1a")
    table_id: str
    # log.debug("Holds the basis or statute, as the EEOC labels it")
    basis: str
    # log.debug("Holds the federal fiscal year, October to September")
    fiscal_year: int
    # log.debug("Holds how many charges cited the basis that year")
    receipts: int
    # log.debug("Holds where the file came from")
    source_url: str
    # log.debug("Holds the SHA-256 of the file, so a revision shows")
    source_sha256: str
    # log.debug("Holds when the load that wrote the row started")
    loaded_at: datetime

########################################################################
#                                                                      #
#                         pipelines/formats.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

The apps' file formats, as models: what a loader reads, before it
becomes raw rows. Each model names only the fields a loader uses, and
ignores the rest, such as a case's answer text or an agent's draft, so
those are never parsed into anything. A field a model names but a file
lacks fails the load: the format changed, and a person should look.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from datetime import date, datetime
from typing import Any

# Third-party
from kds.logs import get_logger
from pydantic import BaseModel, ConfigDict, Field

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                             File formats                             #
#                                                                      #
########################################################################
# log.debug("Defines what every format model shares")
class Format(BaseModel):
    """A part of a file, read only for the fields it names."""

    # log.debug("Ignores the fields a loader does not use")
    model_config = ConfigDict(frozen=True, extra="ignore")


# log.debug("Defines a case of the workbench's run format")
class KdsCase(Format):
    """One case: whether it ran, its scores, time and cost."""

    # log.debug("Holds the case's id")
    case_id: str
    # log.debug("Holds its tags")
    tags: list[str] = Field(default_factory=list)
    # log.debug("Holds whether it ran without an error")
    ok: bool
    # log.debug("Holds the error, when it raised one")
    error: str | None = None
    # log.debug("Holds its scores; numbers load, anything else is dropped")
    scores: dict[str, Any] = Field(default_factory=dict)
    # log.debug("Holds how long it took, in milliseconds")
    latency_ms: int | None = None
    # log.debug("Holds what its model calls cost")
    cost_usd: float | None = None
    # log.debug("Holds how many model calls it made")
    calls: int | None = None


# log.debug("Defines a run of the workbench's run format")
class KdsRun(Format):
    """A Grounded Q&A or EEOC run: what ran, when, and every case."""

    # log.debug("Holds the run's name, such as live-hybrid")
    name: str
    # log.debug("Holds the model it called")
    model: str | None = None
    # log.debug("Holds the provider, fake for the offline stand-in")
    provider: str | None = None
    # log.debug("Holds the date of the prices its costs used")
    prices_as_of: date | None = None
    # log.debug("Holds when it started")
    started_at: datetime | None = None
    # log.debug("Holds when it finished")
    finished_at: datetime | None = None
    # log.debug("Holds how many cases raised")
    failures: int | None = None
    # log.debug("Holds the run's own summary")
    summary: dict[str, Any] = Field(default_factory=dict)
    # log.debug("Holds every case")
    results: list[KdsCase]


# log.debug("Defines one model call the intake agent recorded")
class AgentModelCall(Format):
    """One model call: its step, tokens, cost, time and stop reason."""

    # log.debug("Holds the agent's step")
    step: int
    # log.debug("Holds the tokens it read")
    input_tokens: int
    # log.debug("Holds the tokens it wrote")
    output_tokens: int
    # log.debug("Holds what it cost")
    cost_usd: float | None = None
    # log.debug("Holds how long it took, in milliseconds")
    ms: int
    # log.debug("Holds why the model stopped")
    stop_reason: str | None = None


# log.debug("Defines one tool call the intake agent recorded")
class AgentToolCall(Format):
    """One tool call; its arguments and result are not read."""

    # log.debug("Holds its place in the scenario's calls")
    seq: int
    # log.debug("Holds the agent's step")
    step: int
    # log.debug("Holds the tool's name")
    tool: str
    # log.debug("Holds whether it succeeded")
    ok: bool
    # log.debug("Holds the error, blank when there was none")
    error: str = ""
    # log.debug("Holds how long it took, in milliseconds")
    ms: int
    # log.debug("Holds when it was called")
    at: datetime
    # log.debug("Holds the SHA-256 of its result")
    result_sha256: str | None = None


# log.debug("Defines the agent run behind one scenario")
class AgentRun(Format):
    """When the agent's run for a scenario started and finished."""

    # log.debug("Holds when it started")
    started_at: datetime
    # log.debug("Holds when it finished")
    finished_at: datetime


# log.debug("Defines what the intake agent recorded for one scenario")
class AgentDetail(Format):
    """The scenario's agent run and every call it made."""

    # log.debug("Holds the run")
    run: AgentRun
    # log.debug("Holds every model call")
    model_calls: list[AgentModelCall]
    # log.debug("Holds every tool call")
    tool_calls: list[AgentToolCall]


# log.debug("Defines one scenario's record")
class AgentTrace(Format):
    """A scenario's id and what its agent recorded."""

    # log.debug("Holds the scenario's id")
    id: str
    # log.debug("Holds the recorded run and calls")
    detail: AgentDetail


# log.debug("Defines a run of the intake agent's format")
class IntakeRun(Format):
    """An intake run: each scenario as scored, and what it recorded."""

    # log.debug("Holds the run's name")
    name: str
    # log.debug("Holds the model it called")
    model: str | None = None
    # log.debug("Holds the provider, fake for the offline stand-in")
    provider: str | None = None
    # log.debug("Holds the date of the prices its costs used")
    prices_as_of: date | None = None
    # log.debug("Holds the run's own summary")
    summary: dict[str, Any] = Field(default_factory=dict)
    # log.debug("Holds every scenario as scored, which the raw contract checks")
    scenarios: list[dict[str, Any]]
    # log.debug("Holds every scenario's recorded run and calls")
    traces: list[AgentTrace] = Field(default_factory=list)


# log.debug("Defines the settings of a retrieval run")
class RetrievalSettings(Format):
    """The run's embedding model; no other setting is read."""

    # log.debug("Holds the embedding model")
    model: str | None = None


# log.debug("Defines a retrieval run")
class RetrievalRun(Format):
    """Each question's measures under each search mode."""

    # log.debug("Holds the run's settings")
    settings: RetrievalSettings = Field(default_factory=RetrievalSettings)
    # log.debug("Holds each mode's questions, each a mapping of its measures")
    results: dict[str, list[dict[str, Any]]]


# log.debug("Defines a span's ids")
class SpanContext(Format):
    """The span's trace and its own id."""

    # log.debug("Holds the trace's id")
    trace_id: str
    # log.debug("Holds the span's id")
    span_id: str


# log.debug("Defines a span's status")
class SpanStatus(Format):
    """UNSET, OK or ERROR."""

    # log.debug("Holds the status")
    status_code: str


# log.debug("Defines the service that wrote a span")
class SpanResource(Format):
    """The resource's attributes: the service's name and version."""

    # log.debug("Holds the attributes")
    attributes: dict[str, Any] = Field(default_factory=dict)


# log.debug("Defines one span as OpenTelemetry's SDK writes it")
class OtelSpan(Format):
    """One span: its ids, times, status and attributes."""

    # log.debug("Holds the span's name")
    name: str
    # log.debug("Holds its ids")
    context: SpanContext
    # log.debug("Holds its kind, such as SpanKind.CLIENT")
    kind: str
    # log.debug("Holds its parent's id; a trace's root has none")
    parent_id: str | None = None
    # log.debug("Holds when it started")
    start_time: datetime
    # log.debug("Holds when it ended")
    end_time: datetime
    # log.debug("Holds its status")
    status: SpanStatus
    # log.debug("Holds its attributes")
    attributes: dict[str, Any] = Field(default_factory=dict)
    # log.debug("Holds the service that wrote it")
    resource: SpanResource = Field(default_factory=SpanResource)


# log.debug("Defines one model's prices")
class ModelPrices(Format):
    """USD per million input and output tokens."""

    # log.debug("Holds the input price")
    input: float
    # log.debug("Holds the output price")
    output: float


# log.debug("Defines the workbench's price list")
class PriceList(Format):
    """The list's date and each model's prices."""

    # log.debug("Holds the date the prices were checked")
    as_of: date
    # log.debug("Holds each model's prices")
    models: dict[str, ModelPrices]

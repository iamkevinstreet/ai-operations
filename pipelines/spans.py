########################################################################
#                                                                      #
#                          pipelines/spans.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Turns a run's committed trace, one OpenTelemetry span per line, into
rows of the spans table: each span's ids, times and status, and the
GenAI attributes the workbench writes, as of utils v0.6.1.

Prompt and answer text, a retrieval's query and documents, and a tool
call's arguments and result are attributes too; none of them is in
SPAN_ATTRIBUTES, so none reaches the warehouse.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from datetime import datetime
from typing import Any, Final

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from pipelines.formats import OtelSpan
from pipelines.results import run_id_of
from pipelines.rows import SpanRow

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
# log.debug("Sets the prefix OpenTelemetry's SDK writes before a span's kind")
KIND_PREFIX: Final = "SpanKind."
# log.debug("Maps each span column to the attribute the workbench writes")
SPAN_ATTRIBUTES: Final = {
    "operation": "gen_ai.operation.name",
    "provider": "gen_ai.provider.name",
    "request_model": "gen_ai.request.model",
    "response_model": "gen_ai.response.model",
    "input_tokens": "gen_ai.usage.input_tokens",
    "output_tokens": "gen_ai.usage.output_tokens",
    "cost_usd": "gen_ai.usage.cost",
    "error_type": "error.type",
    "tool_name": "gen_ai.tool.name",
    "observation_type": "langfuse.observation.type",
    "eval_case": "kds.eval.case",
}
# log.debug("Sets the attribute that lists a call's finish reasons")
FINISH_REASONS: Final = "gen_ai.response.finish_reasons"
# log.debug("Sets the resource attribute that names the service")
SERVICE_NAME: Final = "service.name"
# log.debug("Sets the resource attribute that gives the service's version")
SERVICE_VERSION: Final = "service.version"
# log.debug("Sets the milliseconds in a second")
MS: Final = 1000


########################################################################
#                                                                      #
#                            Trace parsing                             #
#                                                                      #
########################################################################
# log.debug("Defines the rows of a committed trace")
def parse_spans(
    app: str | None = None,
    path: str | None = None,
    text: str | None = None,
    *,
    loaded_at: datetime | None = None,
) -> list[SpanRow]:
    """Returns one row per span of the trace file, text left out.

    Args:
        app: The app the file is from. Required.
        path: The trace file's path, which names its run. Required.
        text: Its contents, one span's JSON per line. Required.
        loaded_at: When this load started. Required.

    Returns:
        Each span, with its GenAI attributes as columns.
    """
    # log.debug("Takes the app, which the caller must give")
    app = required(app=app)
    # log.debug("Takes the path, which the caller must give")
    path = required(path=path)
    # log.debug("Takes the contents, which the caller must give")
    text = required(text=text)
    # log.debug("Takes the load's time, which the caller must give")
    loaded_at = required(loaded_at=loaded_at)
    # log.debug("Names the parts every row shares")
    part: dict[str, Any] = {"app": app, "run_id": run_id_of(path), "loaded_at": loaded_at}
    # log.debug("Returns a row per line")
    return [
        _span(OtelSpan.model_validate_json(line), part)
        for line in text.splitlines()
        if line.strip()
    ]


# log.debug("Defines one span's row")
def _span(span: OtelSpan | None = None, part: dict[str, Any] | None = None) -> SpanRow:
    """Returns the span's row: ids, times, status and GenAI attributes.

    Args:
        span: The span, as OpenTelemetry's SDK writes it. Required.
        part: The app, run and load time every row shares. Required.

    Returns:
        The row.
    """
    # log.debug("Takes the span, which the caller must give")
    span = required(span=span)
    # log.debug("Takes the shared parts, which the caller must give")
    part = required(part=part)
    # log.debug("Takes the service that wrote it")
    service = span.resource.attributes
    # log.debug("Takes the first finish reason, when the call gave any")
    reasons = span.attributes.get(FINISH_REASONS) or [None]
    # log.debug("Takes each GenAI attribute the row keeps")
    kept: dict[str, Any] = {c: span.attributes.get(name) for c, name in SPAN_ATTRIBUTES.items()}
    # log.debug("Returns the row")
    return SpanRow(
        **part,
        trace_id=span.context.trace_id,
        span_id=span.context.span_id,
        parent_id=span.parent_id,
        span_name=span.name,
        span_kind=span.kind.removeprefix(KIND_PREFIX),
        started_at=span.start_time,
        ended_at=span.end_time,
        duration_ms=(span.end_time - span.start_time).total_seconds() * MS,
        status_code=span.status.status_code,
        service_name=service.get(SERVICE_NAME),
        service_version=service.get(SERVICE_VERSION),
        finish_reason=reasons[0],
        **kept,
    )

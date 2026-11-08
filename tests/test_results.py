########################################################################
#                                                                      #
#                        tests/test_results.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Tests the parsing of each committed file into raw rows: which files are
runs, each format's rows, the text the spans leave out, the price list,
and a format change failing loudly instead of loading half a row.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Final

# Third-party
import pytest
from kds.args import required
from kds.logs import get_logger
from pydantic import ValidationError

# Local
from pipelines.github import GitFile
from pipelines.prices import parse_prices
from pipelines.results import kind_of, parse_run, run_at_of, run_id_of
from pipelines.spans import parse_spans
from support import FIXTURES, PIN

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
# log.debug("Sets the time every test's load is stamped with")
AT: Final = datetime(2026, 11, 8, tzinfo=UTC)
# log.debug("Sets the folder the apps commit their runs to")
RESULTS: Final = "data/evals/results"


########################################################################
#                                                                      #
#                            Parsing tests                             #
#                                                                      #
########################################################################
# log.debug("Defines one fixture run file's rows")
def _rows(app: str | None = None, name: str | None = None) -> dict[str, list[Any]]:
    """Parses the app's fixture file as a run file.

    Args:
        app: The app's fixture folder. Required.
        name: The file's name. Required.

    Returns:
        The rows by table.
    """
    # log.debug("Takes the app, which the caller must give")
    app = required(app=app)
    # log.debug("Takes the file's name, which the caller must give")
    name = required(name=name)
    # log.debug("Reads and parses the file")
    text = (FIXTURES / app / name).read_text(encoding="utf-8")
    # log.debug("Returns its rows")
    return parse_run(app, GitFile(f"{RESULTS}/{name}", "b" * 40), text, commit=PIN, loaded_at=AT)


# log.debug("Defines the test of which files are runs")
def test_only_run_and_trace_files_are_read() -> None:
    """The index and figures are passed over; retrieval is a kind."""
    # log.debug("Checks each kind")
    assert [
        kind_of(f"{RESULTS}/{name}")
        for name in (
            "live-20261107T203722Z.json",
            "live-20261107T203722Z.spans.jsonl",
            "retrieval-20261107T203618Z.json",
            "index.json",
            "figures.json",
            "live-latest.md",
        )
    ] == ["run", "trace", "retrieval", None, None, None]


# log.debug("Defines the test of a run's id and time")
def test_a_run_and_its_trace_share_an_id_and_a_time() -> None:
    """A run's two files give one id, and its stamp is the UTC time."""
    # log.debug("Checks the two files give one id")
    assert {
        run_id_of(f"x/live-hybrid-20261107T204014Z{end}") for end in (".json", ".spans.jsonl")
    } == {"live-hybrid-20261107T204014Z"}
    # log.debug("Checks the time")
    assert run_at_of("live-hybrid-20261107T204014Z") == datetime(
        2026, 11, 7, 20, 40, 14, tzinfo=UTC
    )
    # log.debug("Checks an id without a stamp is refused")
    with pytest.raises(ValueError, match="no time stamp"):
        # log.debug("Reads a run id with no stamp")
        run_at_of("live-latest")


# log.debug("Defines the test of the workbench's format")
def test_a_workbench_run_gives_cases_numeric_scores_tags_and_its_summary() -> None:
    """Values read and expected are not numbers, so they never load."""
    # log.debug("Parses the EEOC fixture")
    rows = _rows("eeoc-charge-intake", "live-claude-sonnet-5-5-20261107T203513Z.json")
    # log.debug("Checks one run row with its source")
    (run,) = rows["runs"]
    # log.debug("Checks the run's format, cases and pin")
    assert (run.run_format, run.cases, run.source_commit) == ("kds", 3, PIN)
    # log.debug("Checks no score is anything but a number")
    assert {s.metric for s in rows["scores"]}.isdisjoint({"values", "gold", "removed"})
    # log.debug("Checks every case has its tags")
    assert {t.case_id for t in rows["case_tags"]} == {c.case_id for c in rows["cases"]}
    # log.debug("Checks the summary's numbers came along")
    assert {s.metric for s in rows["summaries"]} >= {"field_accuracy", "cost_total_usd"}


# log.debug("Defines the test of the intake format")
def test_an_intake_run_gives_scenarios_and_calls_without_their_arguments() -> None:
    """A tool call keeps its name, outcome and time, never its input."""
    # log.debug("Parses the intake fixture")
    rows = _rows("intake-conflicts-agent", "live-20261107T203722Z.json")
    # log.debug("Checks the run counts its scenarios and takes its times from them")
    (run,) = rows["runs"]
    # log.debug("Checks the format, count and start")
    assert (run.run_format, run.cases, run.started_at is not None) == ("intake", 3, True)
    # log.debug("Checks every scenario's calls were read")
    assert {c.case_id for c in rows["agent_model_calls"]} == {"s01", "s11", "s17"}
    # log.debug("Checks no tool call row has an arguments field")
    assert all("arguments" not in c.model_dump() for c in rows["agent_tool_calls"])


# log.debug("Defines the test of a retrieval run")
def test_a_retrieval_run_gives_each_measure_per_mode() -> None:
    """Three questions in each mode; the run counts questions once."""
    # log.debug("Parses the retrieval fixture")
    rows = _rows("grounded-qa", "retrieval-20261107T203618Z.json")
    # log.debug("Checks the count and the modes")
    assert (rows["runs"][0].cases, {r.retrieval_mode for r in rows["retrieval_scores"]}) == (
        3,
        {"keyword", "semantic", "hybrid"},
    )


# log.debug("Defines the test of the spans")
def test_a_span_keeps_its_numbers_and_no_text() -> None:
    """Tokens, cost and times load; no prompt or answer is a column."""
    # log.debug("Reads the Grounded trace")
    name = "live-hybrid-20261107T204014Z.spans.jsonl"
    # log.debug("Parses it")
    spans = parse_spans(
        "grounded-qa",
        f"{RESULTS}/{name}",
        (FIXTURES / "grounded-qa" / name).read_text(),
        loaded_at=AT,
    )
    # log.debug("Takes a model call's span")
    chat = next(s for s in spans if s.operation == "chat")
    # log.debug("Checks it kept its tokens, cost, kind and time")
    assert (
        bool(chat.input_tokens),
        bool(chat.cost_usd),
        chat.span_kind,
        chat.duration_ms > 0,
    ) == (
        True,
        True,
        "CLIENT",
        True,
    )
    # log.debug("Checks no column holds messages or instructions")
    assert not {k for k in chat.model_dump() if "message" in k or "instruction" in k}


# log.debug("Defines the test of the price list")
def test_the_price_list_gives_a_row_per_model() -> None:
    """Each model's two prices, dated by the list's as_of."""
    # log.debug("Parses the fixture price list")
    rows = parse_prices(
        (FIXTURES / "utils" / "pricing.json").read_text(), commit=PIN, loaded_at=AT
    )
    # log.debug("Takes the Sonnet 5.5 row")
    sonnet = next(r for r in rows if r.model == "claude-sonnet-5-5")
    # log.debug("Checks its prices and date")
    assert (sonnet.input_per_mtok, sonnet.output_per_mtok, str(sonnet.prices_as_of)) == (
        2.0,
        10.0,
        "2026-10-15",
    )


# log.debug("Defines the test that a changed format fails the load")
def test_a_new_scenario_field_fails_instead_of_loading_half_a_row() -> None:
    """The raw contract forbids fields it does not know."""
    # log.debug("Reads the intake fixture")
    doc = json.loads(
        (FIXTURES / "intake-conflicts-agent" / "live-20261107T203722Z.json").read_text()
    )
    # log.debug("Adds a field the contract does not have")
    doc["scenarios"][0]["new_measure"] = 1
    # log.debug("Checks the parse is refused")
    with pytest.raises(ValidationError, match="new_measure"):
        # log.debug("Parses the changed file")
        parse_run(
            "intake-conflicts-agent",
            GitFile(f"{RESULTS}/live-20261107T203722Z.json", "c" * 40),
            json.dumps(doc),
            commit=PIN,
            loaded_at=AT,
        )

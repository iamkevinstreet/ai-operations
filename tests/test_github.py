########################################################################
#                                                                      #
#                         tests/test_github.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Tests the reader of pinned commits without the network: a stand-in for
dlt's requests records every call. The token goes to the API only, a
listing keeps the results folder's files, a cut-short listing is
refused, and a file can be read at another commit.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import json
from typing import Any, Final

# Third-party
import pytest
from kds.logs import get_logger
from pydantic import SecretStr

# Local
from pipelines import github
from pipelines.config import AppSettings
from pipelines.github import GitHubReader

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
# log.debug("Sets the pin the tests read at")
PIN: Final = "a" * 40
# log.debug("Sets a tree with a run file, a trace, a file elsewhere and a folder")
TREE: Final = {
    "truncated": False,
    "tree": [
        {"path": "data/evals/results/live-1.json", "type": "blob", "sha": "1" * 40},
        {"path": "data/evals/results/live-1.spans.jsonl", "type": "blob", "sha": "2" * 40},
        {"path": "data/evals/results", "type": "tree", "sha": "3" * 40},
        {"path": "README.md", "type": "blob", "sha": "4" * 40},
    ],
}


########################################################################
#                                                                      #
#                             Reader tests                             #
#                                                                      #
########################################################################
# log.debug("Defines a stand-in response")
class Answer:
    """What the stand-in returns: a JSON body and some bytes."""

    # log.debug("Defines the constructor")
    def __init__(self, body: Any = None) -> None:
        """Keeps the body.

        Args:
            body: The JSON the response holds.
        """
        # log.debug("Keeps the body and its bytes")
        self.body, self.content = body, json.dumps(body).encode()

    # log.debug("Defines the status check, which always passes")
    def raise_for_status(self) -> None:
        """Passes: every stand-in call succeeds."""

    # log.debug("Defines the JSON body")
    def json(self) -> Any:
        """Returns the body.

        Returns:
            The JSON.
        """
        # log.debug("Returns it")
        return self.body


# log.debug("Defines a reader whose calls are recorded")
@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replaces dlt's requests.get with a recorder that returns TREE.

    Args:
        monkeypatch: pytest's way to change the module for one test.

    Returns:
        The recorded calls: each URL and its headers.
    """
    # log.debug("Starts the record")
    seen: list[dict[str, Any]] = []

    # log.debug("Defines the stand-in")
    def get(url: str | None = None, **options: Any) -> Answer:
        """Records the call and answers with the tree.

        Args:
            url: The address asked for.
            **options: The call's headers, parameters and timeout.

        Returns:
            The stand-in response.
        """
        # log.debug("Records the call")
        seen.append({"url": url, **options})
        # log.debug("Returns the stand-in response")
        return Answer(TREE)

    # log.debug("Puts the stand-in in place")
    monkeypatch.setattr(f"{github.__name__}.requests.get", get)
    # log.debug("Returns the record")
    return seen


# log.debug("Defines a reader with a token")
def _reader() -> GitHubReader:
    """Returns a reader of one app, holding a token.

    Returns:
        The reader.
    """
    # log.debug("Builds it")
    return GitHubReader(AppSettings(github_token=SecretStr("t0ken")), pins={"app": PIN})


# log.debug("Defines the test of the listing")
def test_a_listing_keeps_the_folders_files_and_signs_in(calls: list[dict[str, Any]]) -> None:
    """The run file and its trace; the token on the API call.

    Args:
        calls: The recorded calls.
    """
    # log.debug("Lists the results folder")
    files = _reader().files("app", "data/evals/results")
    # log.debug("Checks only the folder's two files came back")
    assert [f.sha for f in files] == ["1" * 40, "2" * 40]
    # log.debug("Checks the API call was signed in, at the pin")
    assert (calls[0]["headers"]["Authorization"], calls[0]["url"].endswith(PIN)) == (
        "Bearer t0ken",
        True,
    )


# log.debug("Defines the test of a raw read")
def test_a_file_is_read_without_the_token_at_the_commit_asked(calls: list[dict[str, Any]]) -> None:
    """Raw files need no sign-in; a commit given overrides the pin.

    Args:
        calls: The recorded calls.
    """
    # log.debug("Reads at another commit")
    _reader().read("app", "pricing.json", commit="b" * 40)
    # log.debug("Checks the address and that no token went with it")
    assert ("b" * 40 in calls[0]["url"], "Authorization" in calls[0]["headers"]) == (True, False)


# log.debug("Defines the test that a truncated tree is refused")
def test_a_truncated_listing_is_refused(
    calls: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Part of a commit is never loaded as the whole of it.

    Args:
        calls: The recorded calls.
        monkeypatch: pytest's way to change the tree for one test.
    """
    # log.debug("Marks the tree as cut short")
    monkeypatch.setitem(TREE, "truncated", True)
    # log.debug("Checks the listing fails")
    with pytest.raises(RuntimeError, match="truncated"):
        # log.debug("Lists the folder")
        _reader().files("app", "data/evals/results")

########################################################################
#                                                                      #
#                          tests/conftest.py                           #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Runs every test from the repository's root, where config/config.toml
and the dbt project are found, with dlt's telemetry off and no GitHub
token in the environment, so a test never signs in anywhere.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
import pytest
from kds.logs import get_logger

# Local
from support import REPO

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                             Test set-up                              #
#                                                                      #
########################################################################
# log.debug("Defines the set-up every test runs in")
@pytest.fixture(autouse=True)
def _at_the_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Moves to the repository's root and clears what could call out.

    Args:
        monkeypatch: pytest's way to change the process for one test.
    """
    # log.debug("Moves to the root")
    monkeypatch.chdir(REPO)
    # log.debug("Turns dlt's usage telemetry off")
    monkeypatch.setenv("RUNTIME__DLTHUB_TELEMETRY", "false")
    # log.debug("Removes any GitHub token the shell has")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

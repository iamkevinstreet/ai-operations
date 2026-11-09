########################################################################
#                                                                      #
#                        tests/test_compose.py                         #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-09
Last modified on:  2026-11-09

Tests the local Airflow's build without starting it: every Compose
image and both of the Dockerfile's bases name a version, so a later
pull or build cannot change under the project. The Terraform that
provisions where the project runs is in data-platform-aws-databricks.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
import yaml
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
#                            Compose tests                             #
#                                                                      #
########################################################################
# log.debug("Defines the test that every Compose image is pinned")
def test_every_compose_image_names_a_version() -> None:
    """latest, or no tag at all, would change under a later pull."""
    # log.debug("Reads the Compose file")
    compose = yaml.safe_load((REPO / "compose.yaml").read_text(encoding="utf-8"))
    # log.debug("Lists each service's image")
    images = [s["image"] for s in compose["services"].values() if "image" in s]
    # log.debug("Checks each has a tag that is not latest")
    assert images and all(":" in i and not i.endswith(":latest") for i in images)


# log.debug("Defines the test that the image's bases are pinned")
def test_the_airflow_image_builds_on_pinned_bases() -> None:
    """Airflow and uv at fixed versions; no FROM without a tag."""
    # log.debug("Reads the Dockerfile's FROM and COPY --from lines")
    bases = [
        word
        for line in (REPO / "Dockerfile").read_text(encoding="utf-8").splitlines()
        for word in line.split()
        if line.startswith(("FROM ", "COPY --from=")) and "/" in word and ":" in word
    ]
    # log.debug("Checks both bases name a version")
    assert [b.removeprefix("--from=") for b in bases] == [
        "apache/airflow:3.4.0-python3.12",
        "ghcr.io/astral-sh/uv:0.13.6",
    ]

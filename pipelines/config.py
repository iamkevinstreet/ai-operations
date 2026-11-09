########################################################################
#                                                                      #
#                         pipelines/config.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-09

Loads every setting the loaders, the build and the DAGs read, typed and
validated. Values come from config/config.toml and secrets from
config/.env; an environment variable overrides either. The warehouse,
dlt's state, dbt and Databricks settings are kds.pipelines', which
every project shares; the GitHub and AI operations ones are this
project's own.

Each field is a `[section] key` of config/config.toml joined by an
underscore: `[warehouse] path` is `warehouse_path`, which WAREHOUSE_PATH
overrides. A nested table is one field: `[ai_ops.apps]` is
`ai_ops_apps`. The GitHub token and the Databricks token are the only
secrets. SETTINGS holds the settings loaded once at import, for the
values modules bind in their Global constants; functions that take
settings still take them, so tests can pass their own.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import re
from functools import lru_cache
from typing import Final, Self

# Third-party
from kds.logs import get_logger
from kds.pipelines import PipelineSettings
from pydantic import Field, SecretStr, model_validator

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
# log.debug("Sets the pattern of a full commit SHA, the only pin accepted")
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
# log.debug("Sets the pattern of a repository's name")
REPOSITORY: Final = re.compile(r"[a-z0-9][a-z0-9-]*")
# log.debug("Sets the utils commit the price list is read at")
UTILS: Final = "97157184471beb28ed129eb52086c36f76ef3e55"
# log.debug("Pins each app's results to its main after the Nov 8 merges")
APPS: Final = {
    "grounded-qa": "5226cbf61bcdf74eb6794e5266d38fc8c1c453de",
    "intake-conflicts-agent": "97d4c52ab7495d2f47491ee7c65cc93cb7ca95b9",
    "eeoc-charge-intake": "bae5b7c9f588a334fad3280e171a8052b2220c03",
}


########################################################################
#                                                                      #
#                               Settings                               #
#                                                                      #
########################################################################
# log.debug("Defines this project's settings: the shared ones and its own")
class AppSettings(PipelineSettings):
    """Every setting the loaders, the build and the DAGs read."""

    # log.debug("Holds GitHub's API, which lists a commit's files")
    github_api: str = "https://api.github.com"
    # log.debug("Holds where GitHub serves a file at a commit")
    github_raw: str = "https://raw.githubusercontent.com"
    # log.debug("Holds whose repositories the results come from")
    github_owner: str = "iamkevinstreet"
    # log.debug("Holds how long one GitHub request may take")
    github_timeout_s: float = Field(default=30.0, gt=0)
    # log.debug("Holds the optional GitHub token, a secret")
    github_token: SecretStr | None = None

    # log.debug("Holds the schema the apps' results load into")
    ai_ops_dataset: str = "raw_ai_ops"
    # log.debug("Holds the folder every app commits its run files to")
    ai_ops_results: str = "data/evals/results"
    # log.debug("Holds the repository the price list lives in")
    ai_ops_prices_repo: str = "utils"
    # log.debug("Holds the price list's path in that repository")
    ai_ops_prices_path: str = "llm/kds/llm/pricing.json"
    # log.debug("Holds every utils commit that holds a version of the price list")
    ai_ops_prices_commits: list[str] = Field(default_factory=lambda: [UTILS])
    # log.debug("Holds each app's pin: its repository's name and commit")
    ai_ops_apps: dict[str, str] = Field(default_factory=lambda: dict(APPS))

    # log.debug("Defines the checks of the pins")
    @model_validator(mode="after")
    def _pins(self) -> Self:
        """Refuses a pin that can move, or an app that is not a name.

        A branch or a short SHA could point somewhere new tomorrow, so
        every pin is a full commit SHA, and every app a repository's
        name. The shared settings refuse Databricks half set up.

        Returns:
            The settings, unchanged.

        Raises:
            ValueError: When a pin or a name is malformed.
        """
        # log.debug("Collects every pin: each app's and each price list's")
        pins = [*self.ai_ops_apps.values(), *self.ai_ops_prices_commits]
        # log.debug("Refuses any pin that is not a full commit SHA")
        if not all(COMMIT.fullmatch(pin) for pin in pins):
            # log.debug("Raises the bad pin's error")
            raise ValueError("every pin must be a full 40-character commit SHA")
        # log.debug("Refuses any app that is not a repository's name")
        if not all(REPOSITORY.fullmatch(app) for app in self.ai_ops_apps):
            # log.debug("Raises the bad name's error")
            raise ValueError("every app must be a repository name")
        # log.debug("Returns the settings")
        return self


# log.debug("Defines the cached settings")
@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    """Returns the settings, read once per process.

    Returns:
        The settings from config/config.toml, config/.env and the
        environment.
    """
    # log.debug("Reads the settings")
    return AppSettings()


# log.debug("Loads the settings once, for the values modules bind at import")
SETTINGS: Final = get_app_settings()

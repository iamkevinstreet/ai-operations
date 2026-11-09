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
config/.env; an environment variable overrides either.

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
from pathlib import Path
from typing import Final, Literal, Self

# Third-party
from kds.logs import get_logger
from kds.settings import Settings
from pydantic import Field, SecretStr, field_validator, model_validator

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
# log.debug("Types the warehouses dlt can load into")
Destination = Literal["duckdb", "databricks"]
# log.debug("Sets the destination that is a single DuckDB file")
DUCKDB: Final = "duckdb"
# log.debug("Sets the pattern of a full commit SHA, the only pin accepted")
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
# log.debug("Sets the pattern of a repository's name")
REPOSITORY: Final = re.compile(r"[a-z0-9][a-z0-9-]*")
# log.debug("Sets the utils commit the shared packages and the price list come from")
UTILS: Final = "97157184471beb28ed129eb52086c36f76ef3e55"
# log.debug("Pins each app's results to its main after the Nov 8 merges")
APPS: Final = {
    "grounded-qa": "5226cbf61bcdf74eb6794e5266d38fc8c1c453de",
    "intake-conflicts-agent": "97d4c52ab7495d2f47491ee7c65cc93cb7ca95b9",
    "eeoc-charge-intake": "bae5b7c9f588a334fad3280e171a8052b2220c03",
}
# log.debug("Sets where the EEOC publishes its charge receipts by basis")
EEOC_RECEIPTS: Final = (
    "https://www.eeoc.gov/sites/default/files/2026-04/"
    "Table_E1a._Charge_Receipts_by_Basis_or_Statute_%28All_Statutes%29"
    "_FY_1997_-_FY_2025_0.xlsx"
)


########################################################################
#                                                                      #
#                               Settings                               #
#                                                                      #
########################################################################
# log.debug("Defines the settings")
class AppSettings(Settings):
    """Every setting the loaders, the build and the DAGs read."""

    # log.debug("Holds where dlt loads: duckdb or databricks")
    warehouse_destination: Destination = DUCKDB
    # log.debug("Holds the DuckDB file dlt loads and dbt builds in")
    warehouse_path: Path = Path("data/generated/warehouse.duckdb")
    # log.debug("Holds where dlt keeps each pipeline's state")
    warehouse_state: Path = Path("data/generated/dlt")

    # log.debug("Holds the dbt project, which also holds profiles.yml")
    dbt_project: Path = Path("dbt")
    # log.debug("Holds the dbt target: dev for DuckDB, prod for Databricks")
    dbt_target: str = "dev"
    # log.debug("Holds how many models dbt builds at once")
    dbt_threads: int = Field(default=4, ge=1, le=16)

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

    # log.debug("Holds the schema the EEOC's statistics load into")
    eeoc_stats_dataset: str = "raw_eeoc_stats"
    # log.debug("Holds where the EEOC publishes its receipts table")
    eeoc_stats_url: str = EEOC_RECEIPTS
    # log.debug("Holds how long the table's download may take")
    eeoc_stats_timeout_s: float = Field(default=60.0, gt=0)

    # log.debug("Holds the Unity Catalog catalog every schema lives in")
    databricks_catalog: str = "kds"
    # log.debug("Holds the Databricks workspace's host")
    databricks_host: str | None = None
    # log.debug("Holds the Databricks SQL warehouse's HTTP path")
    databricks_http_path: str | None = None
    # log.debug("Holds the Databricks token, a secret")
    databricks_token: SecretStr | None = None

    # log.debug("Holds the text encoding of every file read or written")
    files_encoding: str = "utf-8"

    # log.debug("Defines the host as a name, whichever way it was pasted")
    @field_validator("databricks_host")
    @classmethod
    def _host(cls, host: str | None = None) -> str | None:
        """Strips a scheme and a trailing slash from the host.

        dbt and dlt take the bare host name; a browser shows https://
        in front of it.

        Args:
            host: The host as set, or None.

        Returns:
            The bare host name, or None.
        """
        # log.debug("Returns the host without its scheme or a trailing slash")
        return host.removeprefix("https://").rstrip("/") if host else host

    # log.debug("Defines the checks across fields")
    @model_validator(mode="after")
    def _check(self) -> Self:
        """Refuses a pin that can move, or Databricks half set up.

        A branch or a short SHA could point somewhere new tomorrow, so
        every pin is a full commit SHA, and every app a repository's
        name.

        Returns:
            The settings, unchanged.

        Raises:
            ValueError: When a pin or a name is malformed, or Databricks
                is the destination without its host, path and token.
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
        # log.debug("Lists what a Databricks load needs")
        needed = (self.databricks_host, self.databricks_http_path, self.databricks_token)
        # log.debug("Refuses Databricks without all three")
        if self.warehouse_destination != DUCKDB and not all(needed):
            # log.debug("Raises the missing setup's error")
            raise ValueError("databricks needs DATABRICKS_HOST, _HTTP_PATH and _TOKEN")
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

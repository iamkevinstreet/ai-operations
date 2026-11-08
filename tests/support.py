########################################################################
#                                                                      #
#                           tests/support.py                           #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

What the tests share: the repository's root, a reader that serves the
fixtures folder as if it were each app's pinned commit, and settings
that point the warehouse and dlt's state at a temporary folder.

The fixtures are the apps' real Nov 7 results, cut to a few cases, with
each summary recomputed by the app's own summary code so the cut set
still reconciles, and with prompt, answer and tool text taken out of
the spans.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from pipelines.config import AppSettings
from pipelines.github import GitFile

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
# log.debug("Sets the repository's root, where config/ and dbt/ are")
REPO: Final = Path(__file__).resolve().parents[1]
# log.debug("Sets the folder of fixture files, one folder per app")
FIXTURES: Final = REPO / "tests" / "fixtures"
# log.debug("Sets the commit every fixture app is pinned to, which no repository has")
PIN: Final = "0" * 40
# log.debug("Lists the apps the fixtures hold")
APPS: Final = ("grounded-qa", "intake-conflicts-agent", "eeoc-charge-intake")


########################################################################
#                                                                      #
#                             Test helpers                             #
#                                                                      #
########################################################################
# log.debug("Defines a reader that serves the fixtures as pinned commits")
class FolderReader:
    """Reads tests/fixtures/<app>/ as the app's results folder."""

    # log.debug("Defines the constructor")
    def __init__(self, root: Path = FIXTURES, folder: str | None = None) -> None:
        """Keeps where the fixtures are and the folder they stand for.

        Args:
            root: The fixtures folder, one folder per app.
            folder: The results folder they stand for. Required.
        """
        # log.debug("Keeps the fixtures folder")
        self.root = root
        # log.debug("Takes the folder, which the caller must give")
        self.folder = required(folder=folder)

    # log.debug("Defines the commit every app is read at")
    def commit(self, app: str | None = None) -> str:
        """Returns the one fixture pin.

        Args:
            app: The app; every app has the same pin. Required.

        Returns:
            A commit SHA no repository has.
        """
        # log.debug("Takes the app, which the caller must give")
        required(app=app)
        # log.debug("Returns the pin")
        return PIN

    # log.debug("Defines the listing of an app's fixture files")
    def files(self, app: str | None = None, folder: str | None = None) -> list[GitFile]:
        """Returns each fixture file as a file of the results folder.

        Args:
            app: The app's fixture folder. Required.
            folder: The results folder asked for. Required.

        Returns:
            Each file, with the SHA-1 of its bytes for its blob.
        """
        # log.debug("Takes the app, which the caller must give")
        app = required(app=app)
        # log.debug("Takes the folder, which the caller must give")
        folder = required(folder=folder)
        # log.debug("Lists the app's files under the folder's name")
        return [
            GitFile(f"{folder}/{p.name}", hashlib.sha1(p.read_bytes()).hexdigest())  # noqa: S324
            for p in sorted((self.root / app).iterdir())
        ]

    # log.debug("Defines the reading of one fixture file")
    def read(
        self, app: str | None = None, path: str | None = None, *, commit: str | None = None
    ) -> bytes:
        """Returns the fixture file a path names, whatever the commit.

        Args:
            app: The app's fixture folder. Required.
            path: The file's path; only its name is used. Required.
            commit: Ignored: every fixture has one version.

        Returns:
            The file's bytes.
        """
        # log.debug("Takes the app, which the caller must give")
        app = required(app=app)
        # log.debug("Takes the path, which the caller must give")
        path = required(path=path)
        # log.debug("Reads the file by its name")
        return (self.root / app / Path(path).name).read_bytes()


# log.debug("Defines settings that keep a test's warehouse in its own folder")
def settings_in(folder: Path | None = None) -> AppSettings:
    """Returns the settings with the warehouse and state under folder.

    Args:
        folder: A temporary folder. Required.

    Returns:
        The settings, everything else at its default.
    """
    # log.debug("Takes the folder, which the caller must give")
    folder = required(folder=folder)
    # log.debug("Returns the settings")
    return AppSettings(
        warehouse_path=folder / "warehouse.duckdb",
        warehouse_state=folder / "dlt",
        ai_ops_apps=dict.fromkeys(APPS, PIN),
    )

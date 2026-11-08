########################################################################
#                                                                      #
#                         pipelines/github.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Reads the apps' committed files at pinned commits: the listing from
GitHub's git trees API, each file from raw.githubusercontent.com.

A commit pins exactly what is read, so a load is repeatable: the same
pins give the same rows. A new run reaches the warehouse only when its
app's pin moves, and each row keeps the commit and the git blob it came
from. A token is optional; it only raises GitHub's rate limit.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Protocol

# Third-party
from dlt.sources.helpers import requests
from kds.args import required
from kds.logs import get_logger
from pydantic import BaseModel, ConfigDict
from requests import Response

# Local
from pipelines.config import AppSettings

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
# log.debug("Sets the headers GitHub's API asks every client to send")
API_HEADERS: Final = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "data-platform",
}
# log.debug("Sets the one header a raw file's request sends")
AGENT: Final = {"User-Agent": API_HEADERS["User-Agent"]}
# log.debug("Sets the API models' settings: frozen, and blind to fields not used")
LENIENT: Final = ConfigDict(frozen=True, extra="ignore")
# log.debug("Sets the tree entry type that is a file")
BLOB: Final = "blob"


########################################################################
#                                                                      #
#                            Pinned readers                            #
#                                                                      #
########################################################################
# log.debug("Defines one file of a pinned commit")
@dataclass(frozen=True)
class GitFile:
    """One file of a pinned commit.

    Attributes:
        path: The file's path from the repository root.
        sha: Its git blob SHA-1, which names its exact contents.
    """

    # log.debug("Holds the file's path from the repository root")
    path: str
    # log.debug("Holds its git blob SHA-1")
    sha: str


# log.debug("Defines one entry of a commit's tree, as GitHub's API gives it")
class TreeEntry(BaseModel):
    """A file (blob) or a folder (tree) of the commit."""

    # log.debug("Ignores the fields not used, such as mode and size")
    model_config = LENIENT

    # log.debug("Holds the entry's path from the repository root")
    path: str
    # log.debug("Holds its kind: blob for a file, tree for a folder")
    type: str
    # log.debug("Holds its git SHA-1")
    sha: str


# log.debug("Defines a commit's whole tree")
class Tree(BaseModel):
    """Every entry of the commit, and whether GitHub cut the list."""

    # log.debug("Ignores the fields not used, such as the tree's own SHA")
    model_config = LENIENT

    # log.debug("Holds whether GitHub left entries out")
    truncated: bool
    # log.debug("Holds the entries")
    tree: list[TreeEntry]


# log.debug("Defines what every reader can do, so tests can read a folder")
class Reader(Protocol):
    """Lists and reads one app's files at its pinned commit."""

    # log.debug("Declares the commit an app is read at")
    def commit(self, app: str | None = None) -> str:
        """Returns the commit the app is pinned to.

        Args:
            app: The repository's name. Required.

        Returns:
            The full commit SHA.
        """

    # log.debug("Declares the listing of a folder")
    def files(self, app: str | None = None, folder: str | None = None) -> list[GitFile]:
        """Returns every file under the folder at the pinned commit.

        Args:
            app: The repository's name. Required.
            folder: The folder, from the repository root. Required.

        Returns:
            Each file under the folder, with its blob SHA.
        """

    # log.debug("Declares the reading of one file")
    def read(
        self, app: str | None = None, path: str | None = None, *, commit: str | None = None
    ) -> bytes:
        """Returns the file's bytes at the pin, or at the commit given.

        Args:
            app: The repository's name. Required.
            path: The file's path from the repository root. Required.
            commit: A commit to read at instead of the pin.

        Returns:
            The file's contents.
        """


# log.debug("Defines the reader of GitHub repositories at pinned commits")
class GitHubReader:
    """Reads files of the owner's repositories at pinned commits."""

    # log.debug("Defines the constructor")
    def __init__(
        self, settings: AppSettings | None = None, pins: dict[str, str] | None = None
    ) -> None:
        """Keeps the pins and the addresses to read them from.

        Args:
            settings: Where GitHub is, whose repositories, how long to
                wait, and the optional token. Required.
            pins: Each repository's name mapped to its commit. Required.
        """
        # log.debug("Takes the settings, which the caller must give")
        settings = required(settings=settings)
        # log.debug("Takes the pins, which the caller must give")
        self.pins = required(pins=pins)
        # log.debug("Keeps the settings")
        self.settings = settings
        # log.debug("Takes the token's value, blank when there is none")
        token = settings.github_token.get_secret_value() if settings.github_token else ""
        # log.debug("Adds it to the API's headers only: raw files need no sign-in")
        self.api_headers = API_HEADERS | ({"Authorization": f"Bearer {token}"} if token else {})

    # log.debug("Defines the commit an app is read at")
    def commit(self, app: str | None = None) -> str:
        """Returns the commit the app is pinned to.

        Args:
            app: The repository's name. Required.

        Returns:
            The full commit SHA.
        """
        # log.debug("Takes the app, which the caller must give")
        app = required(app=app)
        # log.debug("Returns its pin")
        return self.pins[app]

    # log.debug("Defines the listing of a folder at the pin")
    def files(self, app: str | None = None, folder: str | None = None) -> list[GitFile]:
        """Returns every file under the folder, from one API call.

        Args:
            app: The repository's name. Required.
            folder: The folder, from the repository root. Required.

        Returns:
            Each file under the folder, with its blob SHA.

        Raises:
            RuntimeError: When GitHub truncated the listing, which would
                load part of a commit and call it whole.
        """
        # log.debug("Takes the app, which the caller must give")
        app = required(app=app)
        # log.debug("Takes the folder, which the caller must give")
        folder = required(folder=folder)
        # log.debug("Builds the tree's address at the pin")
        owner = self.settings.github_owner
        # log.debug("Asks for the whole tree in one call")
        url = f"{self.settings.github_api}/repos/{owner}/{app}/git/trees/{self.pins[app]}"
        # log.debug("Fetches it")
        response = self._get(url, params={"recursive": "1"}, headers=self.api_headers)
        # log.debug("Reads the tree")
        tree = Tree.model_validate_json(response.content)
        # log.debug("Refuses a listing GitHub cut short")
        if tree.truncated:
            # log.debug("Raises the truncated listing's error")
            raise RuntimeError(f"GitHub truncated the file list of {app}")
        # log.debug("Keeps the files under the folder")
        return [
            GitFile(entry.path, entry.sha)
            for entry in tree.tree
            if entry.type == BLOB and entry.path.startswith(f"{folder}/")
        ]

    # log.debug("Defines the reading of one file at the pin")
    def read(
        self, app: str | None = None, path: str | None = None, *, commit: str | None = None
    ) -> bytes:
        """Returns the file's bytes at the pin, or at the commit given.

        Args:
            app: The repository's name. Required.
            path: The file's path from the repository root. Required.
            commit: A full commit SHA to read at instead of the pin, for
                a file kept in several versions, such as the price list.

        Returns:
            The file's contents.
        """
        # log.debug("Takes the app, which the caller must give")
        app = required(app=app)
        # log.debug("Takes the path, which the caller must give")
        path = required(path=path)
        # log.debug("Builds the file's address at the commit")
        base = f"{self.settings.github_raw}/{self.settings.github_owner}/{app}"
        # log.debug("Fetches and returns it")
        return self._get(f"{base}/{commit or self.pins[app]}/{path}", headers=AGENT).content

    # log.debug("Defines one GET, with dlt's retries and the timeout")
    def _get(
        self,
        url: str | None = None,
        params: dict[str, str] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Fetches the address, raising for any status but success.

        Args:
            url: The address. Required.
            params: The query parameters, if any.
            headers: The request's headers. Required.

        Returns:
            The response.
        """
        # log.debug("Takes the address, which the caller must give")
        url = required(url=url)
        # log.debug("Takes the headers, which the caller must give")
        headers = required(headers=headers)
        # log.debug("Fetches it with retries on failures that can pass")
        response = requests.get(
            url, params=params, headers=headers, timeout=self.settings.github_timeout_s
        )
        # log.debug("Raises for any status but success")
        response.raise_for_status()
        # log.debug("Returns the response")
        return response

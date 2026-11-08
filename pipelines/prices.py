########################################################################
#                                                                      #
#                         pipelines/prices.py                          #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-08
Last modified on:  2026-11-08

Turns one version of the workbench's price list into rows: each model's
list price per million input and output tokens, dated by the list.
Every version is kept, so a call is priced at the list valid on its
run's date.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from datetime import datetime

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from pipelines.formats import PriceList
from pipelines.rows import PriceRow

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)


########################################################################
#                                                                      #
#                              Price list                              #
#                                                                      #
########################################################################
# log.debug("Defines the rows of one version of the price list")
def parse_prices(
    text: str | None = None, *, commit: str | None = None, loaded_at: datetime | None = None
) -> list[PriceRow]:
    """Returns one row per model in the workbench's price list.

    Args:
        text: The price list's JSON. Required.
        commit: The utils commit it was read at. Required.
        loaded_at: When this load started. Required.

    Returns:
        Each model's input and output price per million tokens.
    """
    # log.debug("Takes the contents, which the caller must give")
    text = required(text=text)
    # log.debug("Takes the commit, which the caller must give")
    commit = required(commit=commit)
    # log.debug("Takes the load's time, which the caller must give")
    loaded_at = required(loaded_at=loaded_at)
    # log.debug("Reads the list")
    table = PriceList.model_validate_json(text)
    # log.debug("Returns a row per model")
    return [
        PriceRow(
            model=model,
            input_per_mtok=prices.input,
            output_per_mtok=prices.output,
            prices_as_of=table.as_of,
            source_commit=commit,
            loaded_at=loaded_at,
        )
        for model, prices in table.models.items()
    ]

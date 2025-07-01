"""
High–level interface for Investor Follow Tracker
"""
from importlib.metadata import version

from .cli import run           # noqa: F401  (exported for `python -m`)
from .scraping.infinite_scroll import scrape  # convenience
from .processing.csv_to_sheet import push_to_gsheet

__all__ = ["scrape", "push_to_sheet", "run"]
__version__ = version(__name__)

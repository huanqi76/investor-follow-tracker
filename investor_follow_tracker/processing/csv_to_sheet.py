#!/usr/bin/env python3
"""
Usage:
    python csv_to_sheet.py messy_interests.csv
Reads the CSV produced by an earlier run, removes follower-count rows,
replaces the full LinkedIn URLs with just the profile handle, and appends
the cleaned rows to the *data* tab in Google Sheet.

Relies on the helper functions already defined in tools.py:
    - clean_rows(raw_rows)
    - push_to_gsheet(rows)
"""

import sys, csv, pathlib
from investor_follow_tracker.utils import clean_rows, push_to_gsheet

def main(csv_path: str):
    if not pathlib.Path(csv_path).is_file():
        sys.exit(f"File not found: {csv_path}")

    # 1. read the raw CSV  (assumes utf-8 and three columns: url, text, date)
    with open(csv_path, newline="", encoding="utf-8") as f:
        raw_rows = list(csv.reader(f))

    # 2. clean: strip handle + drop follower lines
    rows_for_sheet = clean_rows(raw_rows)
    if not rows_for_sheet:
        sys.exit("Nothing to append: all rows were follower counts or empty.")

    # 3. push to Google Sheets
    import asyncio
    asyncio.run(push_to_gsheet(rows_for_sheet))
    print(f"✓ pushed {len(rows_for_sheet)} cleaned rows to Google Sheets")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python csv_to_sheet.py <path/to/your.csv>")
    main(sys.argv[1])

#!/usr/bin/env python3
"""List flights on the organization's record, newest flown first.

    GET /api/v1/flights?asset_id=&pilot_id=&since=&limit=   (area: flights, not metered)

There is no cursor on this endpoint: narrow the list with --since, --aircraft-id
and --pilot-id, and raise --limit (at most 2,000) when you need more rows.
"""
import argparse
import csv
import sys

import _rotorlab as rl

#: A cell starting with one of these is read as a formula by a spreadsheet.
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """A CSV cell that a spreadsheet shows as text, never runs as a formula:
    a record's site or remarks may be typed by anyone who files a flight."""
    if value is None:
        return ""
    if isinstance(value, str) and value.startswith(FORMULA_START):
        return "'" + value
    return value


COLUMNS = ("id", "flown_at", "asset_id", "pilot_id", "pilot_name", "duration_s",
           "flight_type", "site", "external_ref")


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    parser.add_argument("--aircraft-id", type=int, help="only flights on this aircraft")
    parser.add_argument("--pilot-id", type=int, help="only flights flown by this pilot")
    parser.add_argument("--since", help="only flights flown on or after this date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=50,
                        help="how many, newest first (default 50, at most 2000)")
    parser.add_argument("--csv", action="store_true", help="write CSV to standard output")
    args = parser.parse_args()
    if not 1 <= args.limit <= 2000:
        parser.error("--limit must be between 1 and 2000")
    key = rl.api_key()

    data, _ = rl.request("GET", "flights", key, url=args.url,
                         params={"asset_id": args.aircraft_id, "pilot_id": args.pilot_id,
                                 "since": args.since, "limit": args.limit})
    if args.json:
        rl.print_json(data)
        return
    rows = data.get("flights") or []
    if args.csv:
        out = csv.writer(sys.stdout)
        out.writerow(COLUMNS)
        for f in rows:
            out.writerow([safe_cell(f.get(c, "")) for c in COLUMNS])
        return
    for f in rows:
        minutes = float(f.get("duration_s") or 0) / 60.0
        print("#%-6s %-12s aircraft %-5s %6.1f min  %-18s %s"
              % (f.get("id"), f.get("flown_at") or "", f.get("asset_id") or "-",
                 minutes, (f.get("pilot_name") or "")[:18], f.get("site") or ""))
    print("%d flight(s)" % len(rows))


if __name__ == "__main__":
    rl.run(main)

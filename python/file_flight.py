#!/usr/bin/env python3
"""Record a flight that has been flown on the organization's record.

    POST /api/v1/flights   (area: flights, not metered)

This files a record of a flight after it happened, the way a ground station
does when a flight ends. It does not request, authorize or clear a flight.

`--ref` is your own id for the flight. Sending the same reference again from
the same key corrects that flight in place instead of filing a second copy,
so it is safe to retry after a dropped connection. The key must be read and
write, and its holder needs a role that files flights.

Example:
    python file_flight.py --aircraft-id 4 --minutes 18.5 --date 2026-11-14 \\
        --type inspection --site "North substation" --ref station7-000123
"""
import argparse
import datetime
import uuid

import _rotorlab as rl

FLIGHT_TYPES = ("commercial", "training", "proficiency", "maintenance", "survey",
                "inspection", "public_safety", "test", "recreational", "other")


def build_body(args):
    """The JSON body POST /flights takes, from the command line."""
    body = {"external_ref": args.ref or "example-" + uuid.uuid4().hex[:16],
            "duration_min": args.minutes,
            "flown_at": args.date or datetime.date.today().isoformat(),
            "flight_type": args.type}
    if args.aircraft_id is not None:
        body["asset_id"] = args.aircraft_id
    else:
        body["asset_name"] = args.aircraft_name
    if args.type == "other":
        body["flight_type_other"] = args.type_other
    optional = {"pilot_id": args.pilot_id, "site": args.site,
                "landings": args.landings, "remarks": args.remarks}
    for field, value in optional.items():
        if value is not None:
            body[field] = value
    if args.night:
        body["night"] = True
    return body


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--aircraft-id", type=int,
                       help="a registered aircraft's id (see list_aircraft.py)")
    which.add_argument("--aircraft-name",
                       help="free text for an airframe that is not on the register")
    parser.add_argument("--minutes", type=float, required=True, help="flight time in minutes")
    parser.add_argument("--date", help="when it was flown, ISO 8601 (default: today)")
    parser.add_argument("--type", choices=FLIGHT_TYPES, default="commercial",
                        help="what the flight was for (default: commercial)")
    parser.add_argument("--type-other", help="one line saying what an 'other' flight was for")
    parser.add_argument("--ref", help="your own id for this flight; reuse it to correct the flight")
    parser.add_argument("--pilot-id", type=int,
                        help="who flew it (see list_pilots.py); default: the key's holder")
    parser.add_argument("--site", help="where it was flown")
    parser.add_argument("--landings", type=int, help="number of landings")
    parser.add_argument("--night", action="store_true", help="flown at night")
    parser.add_argument("--remarks", help="free-text remarks")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the request body and send nothing")
    args = parser.parse_args()
    if args.minutes <= 0:
        parser.error("--minutes must be more than 0")
    if args.type == "other" and not args.type_other:
        parser.error("--type other needs --type-other")
    if args.type != "other" and args.type_other:
        parser.error("--type-other goes only with --type other")

    body = build_body(args)
    if args.dry_run:
        rl.print_json(body)
        return
    key = rl.api_key()
    data, _ = rl.request("POST", "flights", key, url=args.url, body=body)
    if args.json:
        rl.print_json(data)
        return

    print("Flight %s on record (your reference: %s)" % (data.get("id"), data.get("external_ref")))
    if data.get("voided"):
        print("That reference names a flight that was voided; the void stands. %s"
              % (data.get("message") or ""))
    if data.get("reference_conflict"):
        print("Note: %s" % data.get("reference_note", "another sender used this reference."))
    for note in ("pilot_note", "pack_note", "crew_note", "pic_note", "duplicate_note"):
        if data.get(note):
            print("%s: %s" % (note, data[note]))
    for wo in data.get("work_raised") or []:
        print("Work order raised: #%s %s (%s)" % (wo.get("id"), wo.get("title"), wo.get("priority")))


if __name__ == "__main__":
    rl.run(main)

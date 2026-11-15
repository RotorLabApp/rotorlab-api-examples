#!/usr/bin/env python3
"""Read one aircraft's record: register entry, health flags and recent flights.

    GET /api/v1/aircraft          the register entry (area: flights)
    GET /api/v1/health/{id}       health flags and the readiness reading (area: flights)
    GET /api/v1/flights?asset_id= its most recent flights (area: flights)

None of these calls is metered. Name the aircraft by its RotorLab id, name,
registration or serial.

The readiness reading summarizes what the organization's own records show.
It is information for the people responsible for the aircraft. It does not
authorize, approve or clear a flight.
"""
import argparse

import _rotorlab as rl


def find_aircraft(rows, wanted):
    wanted_l = wanted.strip().lower()
    for a in rows:
        if str(a.get("id")) == wanted_l:
            return a
    for a in rows:
        for field in ("name", "registration", "serial"):
            if (a.get(field) or "").strip().lower() == wanted_l:
                return a
    return None


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    parser.add_argument("aircraft", help="the aircraft's id, name, registration or serial")
    parser.add_argument("--flights", type=int, default=5,
                        help="how many recent flights to list (default 5, at most 2000)")
    args = parser.parse_args()
    if not 1 <= args.flights <= 2000:
        parser.error("--flights must be between 1 and 2000")
    key = rl.api_key()

    register, _ = rl.request("GET", "aircraft", key, url=args.url)
    craft = find_aircraft(register.get("aircraft") or [], args.aircraft)
    if craft is None:
        parser.exit(1, "No aircraft on the register matches %r.\n" % args.aircraft)
    health, _ = rl.request("GET", "health/%d" % int(craft["id"]), key, url=args.url)
    flights, _ = rl.request("GET", "flights", key, url=args.url,
                            params={"asset_id": craft["id"], "limit": args.flights})
    if args.json:
        rl.print_json({"aircraft": craft, "health": health, "flights": flights})
        return

    print("%s  (id %s)" % (craft.get("name"), craft.get("id")))
    print("  Registration: %s   Serial: %s   Model: %s"
          % (craft.get("registration") or "-", craft.get("serial") or "-",
             craft.get("model") or "-"))
    print("  Status: %s   Flights on record: %s   Hours: %s"
          % (craft.get("status") or "-", craft.get("total_flights"), craft.get("hours")))

    aw = health.get("airworthiness") or {}
    print("")
    print("What the records show (information, not a clearance to fly):")
    print("  Readiness state: %s   (%s)" % (aw.get("state"), aw.get("readiness") or ""))
    if aw.get("judged") is False:
        print("  Not enough on record to judge this aircraft.")
    for reason in aw.get("reasons") or []:
        if isinstance(reason, dict):
            print("  - [%s] %s" % (reason.get("level"), reason.get("text")))
    if aw.get("missing"):
        print("  Not on record yet: %s" % ", ".join(aw["missing"]))
    print("  Health flags from %s measured flights:" % health.get("flights_used", 0))
    for flag in health.get("flags") or []:
        print("  - [%s] %s" % (flag.get("level"), flag.get("title")))

    print("")
    print("Most recent flights:")
    for f in flights.get("flights") or []:
        minutes = float(f.get("duration_s") or 0) / 60.0
        print("  #%-6s %-12s %6.1f min  %-18s %s"
              % (f.get("id"), f.get("flown_at") or "", minutes,
                 (f.get("pilot_name") or "")[:18], f.get("site") or ""))


if __name__ == "__main__":
    rl.run(main)

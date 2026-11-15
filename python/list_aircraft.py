#!/usr/bin/env python3
"""List the organization's aircraft register.

    GET /api/v1/aircraft   (area: flights, not metered)

A member's key needs a role that reads aircraft.
"""
import argparse

import _rotorlab as rl


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    args = parser.parse_args()
    key = rl.api_key()

    data, _ = rl.request("GET", "aircraft", key, url=args.url)
    if args.json:
        rl.print_json(data)
        return

    rows = data.get("aircraft") or []
    print("%-6s %-20s %-12s %-22s %-10s %8s %8s"
          % ("ID", "NAME", "REG", "MODEL", "STATUS", "FLIGHTS", "HOURS"))
    for a in rows:
        print("%-6s %-20s %-12s %-22s %-10s %8s %8.1f"
              % (a.get("id"), (a.get("name") or "")[:20], (a.get("registration") or "")[:12],
                 (a.get("model") or "")[:22], a.get("status") or "",
                 a.get("total_flights") or 0, float(a.get("hours") or 0)))
    print("%d aircraft" % len(rows))


if __name__ == "__main__":
    rl.run(main)

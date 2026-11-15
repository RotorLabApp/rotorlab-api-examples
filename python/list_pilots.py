#!/usr/bin/env python3
"""List the organization's pilots and where each one's currency stands.

    GET /api/v1/pilots   (area: flights, not metered)

A device credential or an organization admin's key reads every pilot's
currency; another person's key reads its holder's own. The key's holder needs
a role that files flights. The roster carries no email addresses.

Currency is reported so a crew knows where it stands. It is information,
never a reason to refuse or to approve a flight.
"""
import argparse

import _rotorlab as rl

# What the `currency` values mean, in the words of the published API document.
WORDS = {
    "current": "current",
    "due_soon": "due soon",
    "lapsed": "lapsed",
    "not_on_file": "no pilot certificate on file in RotorLab (a record gap, not a lapse)",
    "not_met": "not met",
    "unknown": "unknown",
    "not_aircrew": "not aircrew",
}


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    parser.add_argument("--attention", action="store_true",
                        help="list only pilots whose currency is not current")
    args = parser.parse_args()
    key = rl.api_key()

    data, _ = rl.request("GET", "pilots", key, url=args.url)
    if args.json:
        rl.print_json(data)
        return

    shown = 0
    for p in data.get("pilots") or []:
        cur = p.get("currency")
        if args.attention and cur in (None, "current", "not_aircrew"):
            continue
        shown += 1
        line = "%-6s %-24s %-10s" % (p.get("id"), (p.get("name") or "")[:24], p.get("role") or "")
        if cur is None:
            line += "  currency: not shown to this key"
        else:
            line += "  currency: %s" % WORDS.get(cur, cur)
            if p.get("lapsed"):
                line += "  (ran out: %s)" % ", ".join(p["lapsed"])
        if p.get("last_flight"):
            line += "  last flight %s" % p["last_flight"]
        print(line)
    print("%d pilot(s) listed." % shown)
    if data.get("note"):
        print(data["note"])


if __name__ == "__main__":
    rl.run(main)

#!/usr/bin/env python3
"""Check a key: which RotorLab answers, what the key may reach, and today's quota.

    GET /api/v1/version   (area: status, not metered)
    GET /api/v1/usage     (area: status, not metered)

Both calls are free and work with every key, so this is the first thing to
run when a call is refused.
"""
import argparse

import _rotorlab as rl


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    args = parser.parse_args()
    key = rl.api_key()

    version, _ = rl.request("GET", "version", key, url=args.url)
    usage, _ = rl.request("GET", "usage", key, url=args.url)
    if args.json:
        rl.print_json({"version": version, "usage": usage})
        return

    k = usage.get("key") or {}
    print("Server:     %s %s" % (version.get("name"), version.get("version")))
    print("Key:        %s (%s...)" % (k.get("label") or "unnamed", k.get("prefix", "")))
    print("Areas:      %s" % ("every area" if k.get("unrestricted")
                              else ", ".join(k.get("areas") or [])))
    print("Access:     %s" % ("read only" if k.get("read_only") else "read and write"))
    print("Ends:       %s" % (k.get("expires_at") or "no end date"))
    print("Quota:      %s of %s metered calls left today (UTC); %s credits"
          % (usage.get("remaining"), usage.get("limit"), usage.get("credits")))
    if usage.get("max_file_bytes"):
        print("Log limit:  %d MB per uploaded flight log"
              % (int(usage["max_file_bytes"]) // (1024 * 1024)))


if __name__ == "__main__":
    rl.run(main)

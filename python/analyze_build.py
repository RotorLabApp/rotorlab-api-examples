#!/usr/bin/env python3
"""Run a build through the RotorLab performance engine.

    POST /api/v1/analyze   (area: engine, metered: one unit per call)

The answer's `out` holds the headline figures (all-up weight, thrust to
weight, hover and cruise endurance, currents, top speed) and `checks` holds
[level, message] pairs. GET /api/v1/airframes lists every supported
airframe type. These are engineering estimates for design work.
"""
import argparse

import _rotorlab as rl


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    parser.add_argument("--airframe", default="Quad X", help='airframe type (default "Quad X")')
    parser.add_argument("--motors", type=int, default=4, help="motor count (default 4)")
    parser.add_argument("--prop", type=float, default=7.0,
                        help="propeller diameter in inches (default 7)")
    parser.add_argument("--kv", type=float, default=1700.0, help="motor KV (default 1700)")
    args = parser.parse_args()
    key = rl.api_key()

    body = {"airframe_type": args.airframe, "motor_count": args.motors,
            "prop_diameter_in": args.prop, "motor_kv": args.kv}
    data, headers = rl.request("POST", "analyze", key, url=args.url, body=body)
    if args.json:
        rl.print_json(data)
        return
    out = data.get("out") or {}
    print("All-up weight:   %.0f g" % float(out.get("auw_g") or 0))
    print("Thrust/weight:   %.2f" % float(out.get("twr") or 0))
    print("Hover endurance: %.1f min" % float(out.get("hover_min") or 0))
    for check in data.get("checks") or []:
        if isinstance(check, (list, tuple)) and len(check) == 2:
            print("  [%s] %s" % (check[0], check[1]))
    if headers.get("X-RateLimit-Remaining") is not None:
        print("Calls left today: %s (credits %s)"
              % (headers.get("X-RateLimit-Remaining"), headers.get("X-RateLimit-Credits")))


if __name__ == "__main__":
    rl.run(main)

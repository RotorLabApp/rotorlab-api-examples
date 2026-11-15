#!/usr/bin/env python3
"""Attach a flight log file to a flight already on the record.

    POST /api/v1/flights/{id}/log?name=<file name>   (area: flights, not metered)

The body is the raw log file (not JSON, not a multipart form); RotorLab reads
the format from the file's own bytes. The upload is stored and queued for
reading, and the answer comes back at once: `analysis_state` is `queued` in
the normal case. Re-sending identical bytes for the same flight returns the
existing record. File the flight first (file_flight.py), then attach.

GET /api/v1/usage reports `max_file_bytes`, the largest log one upload may
carry; check_key.py prints it.
"""
import argparse
import os

import _rotorlab as rl


def main():
    parser = rl.add_common_args(argparse.ArgumentParser(description=__doc__.splitlines()[0]))
    parser.add_argument("flight_id", type=int, help="the flight's id, as filing it returned")
    parser.add_argument("log_file", help="path to the log (.bin, .tlog, .ulg, DJI .txt, ...)")
    args = parser.parse_args()
    if not os.path.isfile(args.log_file):
        parser.error("no such file: %s" % args.log_file)
    key = rl.api_key()

    with open(args.log_file, "rb") as fh:
        raw = fh.read()
    data, _ = rl.request("POST", "flights/%d/log" % args.flight_id, key, url=args.url,
                         params={"name": os.path.basename(args.log_file)[:160]},
                         raw=raw, timeout=600)
    if args.json:
        rl.print_json(data)
        return
    state = data.get("analysis_state")
    print("Stored with flight %d. analysis_state: %s" % (args.flight_id, state))
    if data.get("reason"):
        print(data["reason"])


if __name__ == "__main__":
    rl.run(main)

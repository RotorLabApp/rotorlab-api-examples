#!/usr/bin/env python3
"""A minimal receiver for RotorLab webhooks that checks every signature.

Standard library only, Python 3.8 or later.

    ROTORLAB_WEBHOOK_SECRET=<the hook's secret> python receiver.py --port 8080

RotorLab posts each event as a JSON body:

    {"event": "flight.filed", "at": "2026-11-14 18:02:11", "data": {...}}

with these headers:

    X-RotorLab-Signature  sha256=<hex HMAC-SHA256 of the raw body, keyed with the secret>
    X-RotorLab-Event      the event name
    X-RotorLab-Delivery   the delivery's id, the same on every retry
    X-RotorLab-Attempt    1 for the first attempt, then 2, 3 and so on

Verify the signature over the exact bytes received, before parsing them.
Answer with any 2xx status once you have accepted the event; anything else
is retried later with the same body, signature and delivery id.

RotorLab only delivers to https:// endpoints. Run this behind your own TLS
terminating proxy or load balancer, which forwards to the port here.
"""
import argparse
import collections
import hashlib
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MAX_BODY = 1024 * 1024


def expected_signature(secret, body):
    """The X-RotorLab-Signature value RotorLab sends for this raw body."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return "sha256=" + digest


def verify_signature(secret, body, header_value):
    """True when the header matches the body under this secret.
    Compared in constant time."""
    if not secret or not header_value:
        return False
    return hmac.compare_digest(expected_signature(secret, body), header_value.strip())


class SeenDeliveries(object):
    """Remembers recent delivery ids so a retry of an event already handled
    is acknowledged and not acted on twice. In memory only: a real service
    should keep these in its own database."""

    def __init__(self, size=10000):
        self._ids = collections.OrderedDict()
        self._size = size

    def first_time(self, delivery_id):
        if not delivery_id:
            return True
        if delivery_id in self._ids:
            return False
        self._ids[delivery_id] = True
        while len(self._ids) > self._size:
            self._ids.popitem(last=False)
        return True


def handle_event(event, at, data):
    """Put your own logic here. Keep it quick, or hand the work to a queue:
    answer within 10 seconds, or the attempt counts as failed and is retried."""
    print("%s  %s  %s" % (at, event, json.dumps(data, sort_keys=True)))
    sys.stdout.flush()


def make_handler(secret, seen):
    class Handler(BaseHTTPRequestHandler):
        def _answer(self, status, text):
            body = (text + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY:
                self._answer(413, "body too large")
                return
            body = self.rfile.read(length)
            if not verify_signature(secret, body, self.headers.get("X-RotorLab-Signature")):
                self._answer(401, "bad signature")
                return
            if not seen.first_time(self.headers.get("X-RotorLab-Delivery")):
                self._answer(200, "already handled")
                return
            try:
                payload = json.loads(body.decode("utf-8"))
            except ValueError:
                self._answer(400, "not JSON")
                return
            handle_event(payload.get("event") or self.headers.get("X-RotorLab-Event"),
                         payload.get("at"), payload.get("data"))
            self._answer(200, "ok")

        def log_message(self, fmt, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1",
                        help="address to listen on (default 127.0.0.1, behind your TLS proxy)")
    parser.add_argument("--port", type=int, default=8080, help="port to listen on (default 8080)")
    args = parser.parse_args()
    secret = (os.environ.get("ROTORLAB_WEBHOOK_SECRET") or "").strip()
    if not secret:
        sys.stderr.write("Set ROTORLAB_WEBHOOK_SECRET to the secret RotorLab showed "
                         "when you added the webhook.\n")
        sys.exit(2)
    server = HTTPServer((args.host, args.port), make_handler(secret, SeenDeliveries()))
    print("Listening on http://%s:%d/" % (args.host, args.port))
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

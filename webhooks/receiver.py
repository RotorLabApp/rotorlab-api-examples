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

The signature covers the body only, not the headers. So this receiver:

- verifies the signature over the exact bytes received, before parsing them;
- takes the event name and time from the signed body, never from a header;
- drops a repeat by the SHA-256 of the body (identical on every retry), not by
  X-RotorLab-Delivery, which anyone holding one captured delivery could change;
- ignores a delivery whose signed `at` is older than REPLAY_WINDOW_S;
- remembers a delivery only once it was handled, and answers 500 when handling
  failed, so RotorLab tries again;
- serves each connection on its own thread with a socket timeout, so one slow
  client cannot hold up the deliveries behind it.

Answer with any 2xx status once you have accepted the event; anything else
is retried later with the same body and signature.

RotorLab only delivers to https:// endpoints. Run this behind your own TLS
terminating proxy or load balancer, which forwards to the port here.
"""
import argparse
import calendar
import collections
import hashlib
import hmac
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 1024 * 1024
#: Longer than RotorLab's retry schedule (about nine hours). Keep body digests
#: at least this long. If your RotorLab server holds deliveries for longer
#: (offline mode), widen this to match.
REPLAY_WINDOW_S = 24 * 3600
#: Seconds a connection may stall before it is cut off.
SOCKET_TIMEOUT_S = 15


def expected_signature(secret, body):
    """The X-RotorLab-Signature value RotorLab sends for this raw body."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return "sha256=" + digest


def verify_signature(secret, body, header_value):
    """True when the header matches the body under this secret.
    Compared in constant time, as bytes, so an odd header cannot raise."""
    if not secret or not header_value:
        return False
    expected = expected_signature(secret, body).encode("ascii")
    return hmac.compare_digest(expected, header_value.strip().encode("latin-1", "replace"))


def too_old(at, now=None):
    """True when the signed `at` (UTC, "YYYY-MM-DD HH:MM:SS") is outside the
    replay window, or cannot be read."""
    try:
        t = calendar.timegm(time.strptime(at, "%Y-%m-%d %H:%M:%S"))
    except (TypeError, ValueError):
        return True
    return (now if now is not None else time.time()) - t > REPLAY_WINDOW_S


class SeenDeliveries(object):
    """Digests of signed bodies already acted on. The body is identical on
    every retry and is covered by the signature; X-RotorLab-Delivery is not.
    In memory only: a real service keeps these in its own database for
    REPLAY_WINDOW_S."""

    def __init__(self, size=10000):
        self._ids = collections.OrderedDict()
        self._size = size
        self.lock = threading.Lock()

    def seen(self, key):
        return key in self._ids

    def remember(self, key):
        self._ids[key] = True
        while len(self._ids) > self._size:
            self._ids.popitem(last=False)


def handle_event(event, at, data):
    """Put your own logic here. Keep it quick, or hand the work to a queue:
    answer within 10 seconds, or the attempt counts as failed and is retried.
    Raise an exception when the event could not be handled: the receiver then
    answers 500 and RotorLab sends it again later."""
    print("%s  %s  %s" % (at, event, json.dumps(data, sort_keys=True)))
    sys.stdout.flush()


def make_handler(secret, seen, handler=None):
    """The request handler class. `handler` defaults to handle_event."""
    act = handler or (lambda event, at, data: handle_event(event, at, data))

    class Handler(BaseHTTPRequestHandler):
        timeout = SOCKET_TIMEOUT_S      # a client that stalls mid-request is cut off

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
            try:
                payload = json.loads(body.decode("utf-8"))
            except ValueError:
                self._answer(400, "not JSON")
                return
            if not isinstance(payload, dict) or not payload.get("event"):
                self._answer(400, "not a RotorLab event")
                return
            if too_old(payload.get("at")):
                self._answer(200, "too old, ignored")      # signed but stale: a replay
                return
            key = hashlib.sha256(body).hexdigest()
            with seen.lock:
                if seen.seen(key):
                    self._answer(200, "already handled")
                    return
                try:
                    act(payload["event"], payload.get("at"), payload.get("data"))
                except Exception:
                    self._answer(500, "not handled, retry")  # RotorLab tries again
                    return
                seen.remember(key)                           # only once it succeeded
            self._answer(200, "ok")

        def log_message(self, fmt, *args):
            pass

    return Handler


def make_server(host, port, secret, seen=None, handler=None):
    """A threaded server, so one slow connection never blocks another."""
    server = ThreadingHTTPServer((host, port),
                                 make_handler(secret, seen or SeenDeliveries(), handler))
    server.daemon_threads = True
    return server


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
    server = make_server(args.host, args.port, secret)
    print("Listening on http://%s:%d/" % (args.host, args.port))
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

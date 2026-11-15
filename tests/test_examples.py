"""Offline checks for the examples. No network, no key, standard library only.

    python -m unittest discover -s tests -v
"""
import ast
import hashlib
import hmac
import importlib.util
import json
import os
import subprocess
import sys
import unittest

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

    def test_a_repeated_delivery_is_seen_once(self):
        seen = self.recv.SeenDeliveries(size=2)
        self.assertTrue(seen.first_time("7"))
        self.assertFalse(seen.first_time("7"))
        self.assertTrue(seen.first_time("8"))
        self.assertTrue(seen.first_time("9"))
        self.assertTrue(seen.first_time("7"))       # forgotten once the window moved on
        self.assertTrue(seen.first_time(None))      # a test ping has no delivery id


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

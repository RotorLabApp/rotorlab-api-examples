"""Shared helpers for the RotorLab API examples.

Standard library only, Python 3.8 or later. Every example reads two
environment variables:

    ROTORLAB_API_KEY   your API key (required)
    ROTORLAB_URL       your RotorLab address (default https://app.rotorlab.app)

The key is read from the environment only, never from the command line, so
it does not end up in your shell history or a process list.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "https://app.rotorlab.app"
USER_AGENT = "rotorlab-api-examples/1.0.0"


class ApiError(Exception):
    """A refusal from the API: the HTTP status, the parsed JSON body and the
    response headers. `body["error"]` is the sentence that says what to do."""

    def __init__(self, status, body, headers):
        self.status = status
        self.body = body if isinstance(body, dict) else {"error": str(body)}
        self.headers = headers
        super().__init__("HTTP %d: %s" % (status, self.body.get("error", "")))


def base_url(override=None):
    """The API root, for example https://app.rotorlab.app/api/v1."""
    root = (override or os.environ.get("ROTORLAB_URL") or DEFAULT_URL).strip()
    root = root.rstrip("/")
    if root.endswith("/api/v1"):
        root = root[: -len("/api/v1")]
    return root + "/api/v1"


def api_key():
    """The key from ROTORLAB_API_KEY, or exit with a clear message."""
    key = (os.environ.get("ROTORLAB_API_KEY") or "").strip()
    if not key:
        sys.stderr.write(
            "Set ROTORLAB_API_KEY to your API key first. Create one in RotorLab "
            "under Organization, Integrations, API keys.\n")
        sys.exit(2)
    return key


def request(method, path, key, url=None, params=None, body=None, raw=None,
            content_type=None, timeout=60):
    """Call one /api/v1 endpoint and return (parsed JSON, headers).

    `body` is sent as JSON; `raw` is sent as bytes (a flight log). Raises
    ApiError for any 4xx or 5xx answer."""
    target = base_url(url) + "/" + path.lstrip("/")
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            target += "?" + urllib.parse.urlencode(clean)
    headers = {"Authorization": "Bearer " + key,
               "Accept": "application/json",
               "User-Agent": USER_AGENT}
    data = None
    if raw is not None:
        data = raw
        headers["Content-Type"] = content_type or "application/octet-stream"
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(target, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8") or "{}"
            return json.loads(text), dict(resp.headers)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = {"error": text.strip() or e.reason}
        raise ApiError(e.code, parsed, dict(e.headers))


def explain(err):
    """Print a refusal the way a program should read it: the status, the
    sentence, and the fields meant for branching."""
    sys.stderr.write("RotorLab answered %d: %s\n" % (err.status, err.body.get("error", "")))
    for field in ("area", "read_only", "mfa_setup_required", "sso", "quota",
                  "duplicate_of", "token", "status_url"):
        if field in err.body:
            sys.stderr.write("  %s: %s\n" % (field, err.body[field]))
    for header in ("Retry-After", "Allow"):
        value = err.headers.get(header)
        if value:
            sys.stderr.write("  %s: %s\n" % (header, value))


def add_common_args(parser):
    """--url and --json, shared by every example."""
    parser.add_argument("--url", default=None,
                        help="RotorLab address (default: $ROTORLAB_URL, or %s)" % DEFAULT_URL)
    parser.add_argument("--json", action="store_true",
                        help="print the raw JSON answer instead of a summary")
    return parser


def print_json(obj):
    print(json.dumps(obj, indent=2, sort_keys=True))


def run(main):
    """Run an example's main(), turning an API refusal into exit status 1
    and a network failure into exit status 3."""
    try:
        main()
    except ApiError as e:
        explain(e)
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write("Could not reach RotorLab: %s\n" % (e.reason,))
        sys.exit(3)

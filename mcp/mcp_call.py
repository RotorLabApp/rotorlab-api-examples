#!/usr/bin/env python3
"""Talk to RotorLab's MCP endpoint by hand: list its tools or call one.

    POST /mcp   (key area: mcp, "AI assistant (MCP) reads"; read only)

Useful to check a key before you hand it to an AI assistant. Standard
library only, Python 3.8 or later. Reads ROTORLAB_API_KEY and ROTORLAB_URL
(default https://app.rotorlab.app).

    python mcp_call.py list
    python mcp_call.py call fleet_overview
    python mcp_call.py call recent_flights --args '{"limit": 5}'
    python mcp_call.py call aircraft_health --args '{"aircraft": "Survey 1"}'
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = "https://app.rotorlab.app"
PROTOCOL = "2025-06-18"
_LOOPBACK = ("localhost", "127.0.0.1", "::1")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: it would carry the Authorization header to the
    new address."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def endpoint(url=None):
    root = (url or os.environ.get("ROTORLAB_URL") or DEFAULT_URL).strip().rstrip("/")
    parts = urllib.parse.urlsplit(root)
    if parts.scheme != "https" and (parts.hostname or "") not in _LOOPBACK:
        sys.stderr.write("ROTORLAB_URL must start with https:// (plain http is allowed "
                         "only for localhost): the key would cross the network in clear.\n")
        sys.exit(2)
    if root.endswith("/mcp"):
        return root
    return root + "/mcp"


def rpc(url, key, method, params=None, msg_id=1):
    """One JSON-RPC request; returns (HTTP status, parsed answer)."""
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    req = urllib.request.Request(
        endpoint(url), data=json.dumps(message).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream",
                 "MCP-Protocol-Version": PROTOCOL,
                 "User-Agent": "rotorlab-api-examples/1.0.0"})
    try:
        with _OPENER.open(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, {"error": {"code": None, "message": text.strip()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=None,
                        help="RotorLab address (default: $ROTORLAB_URL, or %s)" % DEFAULT_URL)
    sub = parser.add_subparsers(dest="action")
    sub.required = True
    sub.add_parser("list", help="list the tools this key may call")
    call = sub.add_parser("call", help="call one tool")
    call.add_argument("tool", help="the tool's name, as `list` shows it")
    call.add_argument("--args", default="{}", help="the tool's arguments as a JSON object")
    args = parser.parse_args()

    arguments = {}
    if args.action == "call":
        try:
            arguments = json.loads(args.args)
        except ValueError:
            parser.error("--args must be a JSON object")
        if not isinstance(arguments, dict):
            parser.error("--args must be a JSON object")

    key = (os.environ.get("ROTORLAB_API_KEY") or "").strip()
    if not key:
        sys.stderr.write("Set ROTORLAB_API_KEY to an API key that includes the "
                         "'AI assistant (MCP) reads' area.\n")
        sys.exit(2)

    status, init = rpc(args.url, key, "initialize", {
        "protocolVersion": PROTOCOL, "capabilities": {},
        "clientInfo": {"name": "rotorlab-api-examples", "version": "1.0.0"}})
    if "error" in init:
        sys.stderr.write("HTTP %d, JSON-RPC %s: %s\n" % (status, init["error"].get("code"),
                                                        init["error"].get("message")))
        sys.exit(1)

    if args.action == "list":
        status, answer = rpc(args.url, key, "tools/list", {}, msg_id=2)
    else:
        status, answer = rpc(args.url, key, "tools/call",
                             {"name": args.tool, "arguments": arguments}, msg_id=2)
    if "error" in answer:
        err = answer["error"]
        sys.stderr.write("HTTP %d, JSON-RPC %s: %s\n" % (status, err.get("code"), err.get("message")))
        if err.get("data") is not None:
            sys.stderr.write("data: %s\n" % json.dumps(err["data"]))
        sys.exit(1)

    result = answer.get("result") or {}
    if args.action == "list":
        for tool in result.get("tools") or []:
            print("%-24s %s" % (tool.get("name"), tool.get("title") or ""))
        return
    print(json.dumps(result.get("structuredContent", result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

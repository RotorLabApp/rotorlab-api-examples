# Frequently asked questions

### Do I need to install anything?

Python 3.8 or later. The scripts use only the standard library, so there is no `pip install`. The curl examples need curl.

### Where do I get an API key?

In RotorLab, under **Organization, Integrations, API keys**. Your organization decides who may create keys; by default that is organization admins and roles with Integrations (manage).

### Which areas should I tick?

Only the ones the integration needs. For the quick start, `flights` with **Read only** is enough. For an AI assistant, only **AI assistant (MCP) reads**. The README's Areas table says what each area reaches.

### Will running the examples spend my quota or credits?

Records calls are never metered: reading aircraft, pilots and flights, and filing flights, are free. `check_key.py` is free. The engine (`analyze_build.py`), saved builds and uploading a log for forensics spend one unit each, from the daily quota first and then from credits.

### Can I run the examples without changing my records?

Yes. `check_key.py`, `list_aircraft.py`, `aircraft_record.py`, `list_pilots.py` and `list_flights.py` only read. `file_flight.py` and `attach_log.py` write, and need a read-and-write key.

### How do I avoid filing the same flight twice?

Send your own `external_ref` with each flight. Sending the same reference again from the same key corrects that flight in place, so a station can retry safely after a dropped link. Give each station its own key.

### Is there pagination?

The `/api/v1` list endpoints have no cursor: narrow `GET /flights` with `since`, `asset_id` and `pilot_id`, and set `limit` (default 200, at most 2,000). The MCP tool `recent_flights` pages with `next_cursor`.

### Are webhooks in the OpenAPI document?

No. Webhooks are configured in the app and documented in [webhooks/README.md](../webhooks/README.md). They are available with Fleet Manager.

### Can I test a webhook without exposing my laptop to the internet?

RotorLab delivers only to public `https://` addresses. Run `receiver.py` behind a TLS-terminating proxy on a host that is reachable, then use **Test** on the Webhooks card, which sends a `ping` event.

### Can an AI assistant change my records through MCP?

No. The MCP endpoint has no writing tool, and a key with only the MCP area cannot call the rest of the API.

### Can I edit `openapi/openapi.json` or the Postman collection here?

No. They are byte-for-byte copies of RotorLab's published files and keep RotorLab, Inc.'s terms. Fixes to them come from RotorLab's own release; open an issue if something is wrong.

### Does a green readiness reading mean an aircraft may fly?

No. RotorLab records, reminds and warns. A readiness reading or a currency value says what your records show; it never authorizes, approves or clears a flight.

### Does RotorLab only read ArduPilot logs?

No. Supported log formats include ArduPilot, PX4, MAVLink, DJI, Parrot, GUTMA, Blackbox and CSV exports, and the format is detected from the file. The developer page has the full list.

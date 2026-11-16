# Compatibility

"Run for this release" means the example was run against a RotorLab server for this documentation update of release 1.0.0 and worked. "Offline tests" means the test suite checks it (it parses as Python 3.8, imports only the standard library, and parses its arguments) but it was not run against a server. "Supported" means it is written for that platform but nobody ran it there for this update.

## Python and platforms

| | Linux | macOS | Windows |
|---|---|---|---|
| Python 3.8 to 3.13 | Supported | Supported | Supported |
| Python 3.14 | Supported | Supported | Run for this release (Git Bash) |
| Shell examples | bash | bash or zsh | Git Bash or PowerShell, as shown |
| curl examples | curl (7.55 or later for the header-from-standard-input form) | the same | Git Bash; the examples use bash syntax |

## Examples

| Example | What it calls | Status |
|---|---|---|
| `python/check_key.py` | `GET /version`, `GET /usage` | Run for this release |
| `python/list_aircraft.py` | `GET /aircraft` | Run for this release |
| `python/aircraft_record.py` | `GET /health/{id}`, `GET /flights` | Run for this release |
| `python/list_pilots.py` | `GET /pilots` | Run for this release |
| `python/list_flights.py` | `GET /flights` | Run for this release |
| `python/file_flight.py` | `POST /flights` | Offline tests |
| `python/attach_log.py` | `POST /flights/{id}/log` | Offline tests |
| `python/analyze_build.py` | `POST /analyze` (metered) | Offline tests |
| `mcp/mcp_call.py` | `POST /mcp` (`initialize`, `tools/list`, `tools/call`) | Run for this release |
| `webhooks/receiver.py` | Receives webhook deliveries | Run for this release, with locally signed deliveries |
| `curl/README.md` | The same calls as one-liners | Supported |

## RotorLab

| | Detail |
|---|---|
| API version | `/api/v1`, as described by `openapi/openapi.json` (RotorLab 3.5.7). |
| MCP protocol revisions | `2025-06-18`, `2025-03-26` and `2024-11-05`, Streamable HTTP |
| MCP clients | Claude Code (`.mcp.json` or `claude mcp add`), or any client that speaks Streamable HTTP with an `Authorization` header |
| Webhooks | Available with Fleet Manager; configured under Organization, Integrations, Webhooks |
| Postman | The collection in `postman/` is in the Postman v2.1 format |

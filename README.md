# RotorLab API examples

Working examples for the RotorLab API: Python scripts, curl one-liners, a webhook receiver and an MCP setup for AI assistants, plus copies of the published OpenAPI document and Postman collection.

RotorLab is the record system for drone fleets: flights, aircraft, pilots, maintenance and the records an operator keeps. The API is a key-authenticated HTTP interface over the same records and the same performance engine the app uses. Use it to file what your ground stations flew, read your register and your pilots' standing into your own systems, and run builds through the engine from scripts and notebooks.

RotorLab records, reminds and warns. It never authorizes, approves or clears a flight. A readiness reading or a currency value in an API answer says what your organization's records show; the decision to fly stays with the people and authorities responsible for it.

- Developer page: https://rotorlab.app/developers
- Documentation: https://docs.rotorlab.app/
- Talk to us about an integration: https://rotorlab.app/contact-sales

## Quick start

```bash
export ROTORLAB_API_KEY="rl_your_key"           # placeholder: paste your own key
export ROTORLAB_URL="https://app.rotorlab.app"  # the default; change it for your own server

python python/check_key.py           # which server, what the key reaches, today's quota
python python/list_aircraft.py       # the aircraft register
python python/aircraft_record.py "Survey 1"
python python/list_pilots.py         # pilots and where each one's currency stands
```

The scripts need Python 3.8 or later and nothing outside the standard library.

## Get an API key

1. Sign in to RotorLab and open **Organization, Integrations, API keys**.
2. Name the key, tick the areas it needs, choose **read only** or **read and write**, and choose when it ends.
3. Click **Create API key**. The key is shown once: copy it somewhere safe. Keys start with `rl_`.

Who may create keys is the organization's choice. By default it is organization admins and roles with Integrations (manage); an admin can open it to every member, or allow no personal keys at all. The organization also sets the longest a key may last, and its admins see and can revoke every key. A person may hold up to 25 active keys: give each integration its own, so revoking one leaves the others working.

A key acts for the person who holds it. It reaches only what that person's role reaches, and the organization's two-factor and single sign-on rules apply to it.

### Areas

Every key carries `status` (version and usage). The other areas are ticked when the key is created:

| Area | What it reaches |
|---|---|
| `flights` | Flights, aircraft, pilots, sorties, missions (reads), work orders, components, types, service bulletins, health, advisory scores |
| `checklists` | Checklist templates and completed runs |
| `engine` | `analyze`, `rf`, `cg`, `airframes`, `catalog`, and log forensics (`crash`) |
| `builds` | Your own saved builds |
| `missions` | Saving, importing and deleting mission plans |
| `jobs` | Clients and jobs (read only) |
| `mcp` | The MCP endpoint for AI assistants (see [`mcp/`](mcp/)) |
| `live` | The live telemetry relay |

A **read-only** key reads records and runs the engine; it never changes a record.

Ground stations and other equipment use a **device credential** instead of a personal key. It belongs to the organization, so it keeps working after the person who created it leaves, and it reaches the `status`, `flights` and `checklists` areas.

## Base URL and authentication

```
https://app.rotorlab.app/api/v1
```

Send the key as a bearer token:

```bash
curl -H "Authorization: Bearer $ROTORLAB_API_KEY" https://app.rotorlab.app/api/v1/version
```

The header `X-API-Key: <key>` is accepted too. Request and response bodies are JSON, except the two flight log uploads, whose body is the raw file.

## Endpoints used here

| Call | Area | Metered | Example |
|---|---|---|---|
| `GET /version`, `GET /usage` | `status` | no | [`check_key.py`](python/check_key.py) |
| `GET /aircraft` | `flights` | no | [`list_aircraft.py`](python/list_aircraft.py) |
| `GET /health/{id}` with `GET /flights?asset_id=` | `flights` | no | [`aircraft_record.py`](python/aircraft_record.py) |
| `GET /pilots` | `flights` | no | [`list_pilots.py`](python/list_pilots.py) |
| `GET /flights` | `flights` | no | [`list_flights.py`](python/list_flights.py) |
| `POST /flights` | `flights` | no | [`file_flight.py`](python/file_flight.py) |
| `POST /flights/{id}/log` | `flights` | no | [`attach_log.py`](python/attach_log.py) |
| `POST /analyze` | `engine` | yes | [`analyze_build.py`](python/analyze_build.py) |

The same calls as curl one-liners are in [`curl/README.md`](curl/README.md). Every operation (including checklists, missions, work orders, components, types, service bulletins, sorties, jobs, clients, saved builds, radio link budgets, center of gravity and log forensics) is listed in the [OpenAPI document](openapi/) and on the developer page, each with its `x-area` and `x-metered`.

Records are your organization's and builds are your own: anything else answers `404`.

### Filing flights safely

`POST /flights` takes your own `external_ref` for each flight. Sending the same reference again from the same key corrects that flight in place instead of filing a second copy, so a station can retry after a dropped link. Give each station its own key: two stations sharing one key are one sender. File the flight first and attach its log second, so a failed upload never costs the flight record.

## Errors

Every error is JSON with an `error` sentence that says what to do, and, where it helps a program branch, a field beside it.

| Status | Meaning | Branch on |
|---|---|---|
| 400 | A body or value the call cannot read; the error names the field | |
| 401 | No key, or a key that was revoked, has ended, or whose holder's access ended | |
| 402 | An add-on the account lacks, or a plan with no API calls and no credits | `quota: "none"` |
| 403 | The key lacks the area, is read only, the holder's role does not reach it, two-factor or single sign-on is outstanding, or the plan has ended | `area`, `read_only`, `mfa_setup_required`, `sso` |
| 404 | No such record in your organization, or a path that is not an endpoint (never metered) | |
| 405 | The path exists but not with this method; the `Allow` header names the ones it takes | `Allow` |
| 409 | Refused because of the record's state, for example a log already stored with another flight | `duplicate_of` |
| 410 | A queued log reading that has expired | |
| 413 | Over the limit: 4 MB for a JSON body, 64 MB for a forensics log, 512 MB for a log attached to a flight | |
| 429 | Today's quota and credits are spent, or five of your logs are already waiting to be read | `quota: "exhausted"`, `waiting`, `Retry-After` |
| 503 | A forensics log not read in time; collect it later from `status_url` at no further cost | `token`, `status_url` |

The Python examples print the status, the sentence and these fields, and exit with status 1.

## Pagination

The `/api/v1` list endpoints have no cursor. Narrow `GET /flights` with `since` (a date), `asset_id` and `pilot_id`, and set `limit` (default 200, at most 2,000), newest flown first. The MCP tool `recent_flights` pages with `next_cursor`.

## Quotas and rate limits

A metered call spends one unit. The engine, saved builds and uploading a log for forensics are metered. Everything that files or reads your organization's own records is not: flights, checklists, missions, pilots, sorties, aircraft, work orders, components, types, service bulletins, health and scores are free, so filing a record is never stopped by a quota. `version` and `usage` are free too. A refused call and an unknown path spend nothing.

Your plan sets a daily quota, which resets at 00:00 UTC and is spent first; after it, calls draw on your organization's credit balance. When both are spent the API answers `429` with `Retry-After` set to the seconds until the reset. Every metered response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Credits`, and `GET /api/v1/usage` reports the same at any time.

The MCP endpoint spends no quota or credits; each key may send it 60 requests a minute and 1,000 an hour.

## What is in this repository

| Folder | Contents |
|---|---|
| [`python/`](python/) | Standard-library scripts for the calls above |
| [`curl/`](curl/) | The same calls as one-liners |
| [`webhooks/`](webhooks/) | The events RotorLab pushes, the signature scheme, and a receiver that verifies it |
| [`mcp/`](mcp/) | Connecting an AI assistant to RotorLab's read-only MCP endpoint |
| [`openapi/`](openapi/) | The published OpenAPI document, byte for byte |
| [`postman/`](postman/) | The published Postman collection, byte for byte |
| [`tests/`](tests/) | Offline checks of the examples |

Every script reads `ROTORLAB_API_KEY` and `ROTORLAB_URL` from the environment, takes `--help`, and takes `--json` to print the raw answer. Keep your key out of source control: put it in an environment variable or a `.env` file, which `.gitignore` already excludes.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests run offline: they check that each example parses as Python 3.8, imports nothing outside the standard library, and parses its arguments. They make no network call and need no key.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). RotorLab and the RotorLab logo are trademarks of RotorLab, Inc.; the license does not grant rights to them.

Security issues: see [`SECURITY.md`](SECURITY.md). Contributions: see [`CONTRIBUTING.md`](CONTRIBUTING.md).

# Postman collection

`rotorlab.postman_collection.json` is RotorLab's published Postman collection (v2.1 format), copied byte for byte from

    https://app.rotorlab.app/rotorlab.postman_collection.json

which is the "Download Postman collection" link on https://rotorlab.app/developers.

| | |
|---|---|
| Fetched | 2026-11-15 |
| SHA-256 | `b8ea15b83f5e06193d47d95bc89c02a12dd1fbf913046fef1a1c6d6cdf6240a0` |

## Use it

1. In Postman, choose Import and pick `rotorlab.postman_collection.json`.
2. Open the collection's Variables tab and set:
   - `base_url`: your RotorLab address, for example `https://app.rotorlab.app`
   - `api_key`: your key. Put it in the current value only, so it is not synced or exported.
3. Authentication is set once on the collection as a bearer token.

The collection covers version and usage, the engine (airframes, catalog, analyze, rf, cg), saved builds and log forensics. It does not include the records endpoints (flights, aircraft, pilots, maintenance and the rest); the OpenAPI document in `../openapi/` lists every operation, and `../curl/` and `../python/` show the records calls.

This file is not edited here. A correction belongs in RotorLab's published collection first, and this copy is then refreshed from it.

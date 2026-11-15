# Postman collection

`rotorlab.postman_collection.json` is RotorLab's published Postman collection (v2.1 format), part of its published API description, copied as-is, byte for byte, from the developer page https://rotorlab.app/developers ("Download Postman collection"):

    https://app.rotorlab.app/rotorlab.postman_collection.json

| | |
|---|---|
| Source | https://app.rotorlab.app/rotorlab.postman_collection.json |
| SHA-256 | `b8ea15b83f5e06193d47d95bc89c02a12dd1fbf913046fef1a1c6d6cdf6240a0` |
| Matches | RotorLab 3.5.7, the release of the OpenAPI document published beside it |
| Fetched | 2026-11-15 |

**License.** This file is not covered by this repository's Apache License 2.0. It is RotorLab, Inc.'s published API description, it remains RotorLab, Inc.'s, and it keeps its own terms. Use it to build against the RotorLab API.

**The live copy is the reference:** https://app.rotorlab.app/rotorlab.postman_collection.json. To check whether this copy is current:

```bash
curl -s https://app.rotorlab.app/rotorlab.postman_collection.json | sha256sum
```

## Use it

1. In Postman, choose Import and pick `rotorlab.postman_collection.json`.
2. Open the collection's Variables tab and set:
   - `base_url`: your RotorLab address, for example `https://app.rotorlab.app`
   - `api_key`: your key. Put it in the current value only, so it is not synced or exported.
3. Authentication is set once on the collection as a bearer token.

The collection covers version and usage, the engine (airframes, catalog, analyze, rf, cg), saved builds and log forensics. It does not include the records endpoints (flights, aircraft, pilots, maintenance and the rest); the OpenAPI document in `../openapi/` lists every operation, and `../curl/` and `../python/` show the records calls.

This file is not edited here. A correction belongs in RotorLab's published collection first, and this copy is then refreshed from it.

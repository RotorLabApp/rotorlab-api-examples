# OpenAPI document

`openapi.json` is RotorLab's published API description, copied as-is, byte for byte, from the developer page https://rotorlab.app/developers ("Download OpenAPI spec"):

    https://app.rotorlab.app/openapi.json

| | |
|---|---|
| Source | https://app.rotorlab.app/openapi.json (also served at https://app.rotorlab.app/api/v1/openapi.json) |
| SHA-256 | `e5fecb21153c3dff03d6a0802d16cfef0d503473640ce3d0831dda523956156e` |
| Matches | RotorLab 3.5.7 (`info.version` in this copy) |
| Fetched | 2026-11-15 |

**License.** This file is not covered by this repository's Apache License 2.0. It is RotorLab, Inc.'s published API description, it remains RotorLab, Inc.'s, and it keeps its own terms. Use it to build against the RotorLab API.

**The live copy is the reference.** Each RotorLab server fills in its own address under `servers` and its own release under `info.version`, so when the live document and this copy differ, use the live one: https://app.rotorlab.app/openapi.json. To check whether this copy is current:

```bash
curl -s https://app.rotorlab.app/openapi.json | sha256sum
```

Every operation carries two extensions:

- `x-area`: the key area the call needs (`status` comes with every key).
- `x-metered`: whether the call spends a unit of the daily quota or credits.

Import it into editor.swagger.io, a code generator or any HTTP client for a full interactive reference.

This file is not edited here. A correction belongs in RotorLab's published document first, and this copy is then refreshed from it.

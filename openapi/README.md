# OpenAPI document

`openapi.json` is RotorLab's published OpenAPI 3.0.3 document, copied byte for byte from

    https://app.rotorlab.app/openapi.json

which is the "Download OpenAPI spec" link on https://rotorlab.app/developers. The same document is also served at `https://app.rotorlab.app/api/v1/openapi.json`, with no key needed.

| | |
|---|---|
| Fetched | 2026-11-15 |
| `info.version` in this copy | 3.5.7 |
| SHA-256 | `e5fecb21153c3dff03d6a0802d16cfef0d503473640ce3d0831dda523956156e` |

Each RotorLab server fills in its own address under `servers` and its own release under `info.version`, so the live document is the reference when it and this copy differ. To check whether this copy is current:

```bash
curl -s https://app.rotorlab.app/openapi.json | sha256sum
```

Every operation carries two extensions:

- `x-area`: the key area the call needs (`status` comes with every key).
- `x-metered`: whether the call spends a unit of the daily quota or credits.

Import it into editor.swagger.io, a code generator or any HTTP client for a full interactive reference.

This file is not edited here. A correction belongs in RotorLab's published document first, and this copy is then refreshed from it.

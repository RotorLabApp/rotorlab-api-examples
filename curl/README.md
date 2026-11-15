# curl one-liners

The same calls as the Python examples, for a shell. Set two variables first:

```bash
export ROTORLAB_URL="https://app.rotorlab.app"
read -rs ROTORLAB_API_KEY && export ROTORLAB_API_KEY     # paste the key, then Enter
```

Pasting the key at the `read` prompt keeps it out of your shell history. Always use an `https://` address: over plain `http://` the key crosses the network in clear. On a shared machine, note that `-H "Authorization: Bearer $ROTORLAB_API_KEY"` puts the key in curl's command line, which other users can see in a process list; with curl 7.55 or later you can pass the header from standard input instead:

```bash
printf 'Authorization: Bearer %s' "$ROTORLAB_API_KEY" | curl -s -H @- "$ROTORLAB_URL/api/v1/version"
```

Every call sends the key as a bearer token. `X-API-Key: $ROTORLAB_API_KEY` is accepted too.

## Check the key (free, area `status`)

```bash
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/version"
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/usage"
```

`usage.key` shows the key's areas, whether it is read only and when it ends.

## Aircraft register (area `flights`, not metered)

```bash
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/aircraft"
```

## One aircraft's record (area `flights`, not metered)

Health flags and the readiness reading for aircraft `4`, then its five most recent flights:

```bash
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/health/4"
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/flights?asset_id=4&limit=5"
```

The readiness reading (`airworthiness.state`: `go`, `limits`, `advisory`, `unknown` or `no_go`) says what the organization's records show. Parse `state`, read `judged` first, and treat it as information for the people responsible, never as a clearance to fly.

## Pilots and their currency (area `flights`, not metered)

```bash
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/pilots"
```

Currency is reported so a crew knows where it stands. It must never be used to prevent or to approve a flight.

## Flights on record (area `flights`, not metered)

```bash
curl -s -H "Authorization: Bearer $ROTORLAB_API_KEY" "$ROTORLAB_URL/api/v1/flights?since=2026-11-01&limit=50"
```

Filters: `asset_id`, `pilot_id`, `since` (a date), `limit` (default 200, at most 2,000). There is no cursor.

## Record a flight that was flown (area `flights`, read and write key, not metered)

```bash
curl -s -X POST "$ROTORLAB_URL/api/v1/flights" -H "Authorization: Bearer $ROTORLAB_API_KEY" -H "Content-Type: application/json" -d '{"external_ref":"station7-000123","asset_id":4,"duration_min":18.5,"flown_at":"2026-11-14","flight_type":"inspection","site":"North substation"}'
```

Sending the same `external_ref` again from the same key corrects that flight instead of filing a second one, so retries are safe. The answer's `id` is the flight's id.

## Attach the flight's log (area `flights`, not metered)

```bash
curl -s -X POST "$ROTORLAB_URL/api/v1/flights/359/log?name=flight.bin" -H "Authorization: Bearer $ROTORLAB_API_KEY" -H "Content-Type: application/octet-stream" --data-binary @flight.bin
```

The body is the raw file. `flight.bin` is an example name: any supported log format works, and the format is detected from the file itself. Read `analysis_state` in the answer: `queued` is the normal case. A `409` with `duplicate_of` means these bytes are already stored with another flight.

## Analyze a build (area `engine`, metered)

```bash
curl -s -X POST "$ROTORLAB_URL/api/v1/analyze" -H "Authorization: Bearer $ROTORLAB_API_KEY" -H "Content-Type: application/json" -d '{"airframe_type":"Quad X","motor_count":4,"prop_diameter_in":7,"motor_kv":1700}'
```

Add `-i` to see `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Credits`.

## MCP: list the tools (area `mcp`)

```bash
curl -s -X POST "$ROTORLAB_URL/mcp" -H "Authorization: Bearer $ROTORLAB_API_KEY" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
curl -s -X POST "$ROTORLAB_URL/mcp" -H "Authorization: Bearer $ROTORLAB_API_KEY" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"recent_flights","arguments":{"limit":10}}}'
```

# Connect an AI assistant (MCP)

RotorLab serves a read-only [Model Context Protocol](https://modelcontextprotocol.io) endpoint on the same address as the API:

    POST https://app.rotorlab.app/mcp

Point any MCP client that speaks Streamable HTTP (Claude, or your own agent) at it with an API key, and it can ask questions of your organization's records. RotorLab ships no model of its own: the assistant is yours, reading through your key.

## The key

1. In RotorLab, open Organization, Integrations, API keys.
2. Create a key with the **AI assistant (MCP) reads** area ticked. A read-only key is enough: the endpoint never writes.
3. Copy the key when it is shown. It is shown once.

Send it as `Authorization: Bearer <key>`. The key's organization is the boundary for every read. A member's key sees only the tools their role reads, and two-factor and single sign-on rules apply to the key as they do to signing in.

## Claude Code

```bash
export ROTORLAB_API_KEY="rl_your_key"     # placeholder: paste your own key
claude mcp add --transport http rotorlab https://app.rotorlab.app/mcp \
  --header "Authorization: Bearer $ROTORLAB_API_KEY"
```

Or in a project's `.mcp.json`, which reads the key from your environment so it is never written into the file:

```json
{
  "mcpServers": {
    "rotorlab": {
      "type": "http",
      "url": "https://app.rotorlab.app/mcp",
      "headers": {
        "Authorization": "Bearer ${ROTORLAB_API_KEY}"
      }
    }
  }
}
```

Other clients take the same three facts: the URL, the HTTP (Streamable HTTP) transport, and the `Authorization` header.

## Tools

Every tool is a read, with an input schema, an output schema and read-only annotations, so a client can run them without asking. Each result carries `structuredContent` and the same JSON as text.

| Tool | What it reads | Role permission a member's key needs |
|---|---|---|
| `fleet_overview` | The aircraft register with each aircraft's readiness reading; the names other tools take | `aircraft.view` |
| `aircraft_health` | One aircraft's health flags and measured trends (argument: `aircraft`, a name, registration or serial) | `health.view` |
| `recent_flights` | Recent flights, 20 a page by default and at most 50 (`limit`, `cursor`) | `flights.view` |
| `open_work_orders` | Open work orders | `maintenance.view` |
| `open_occurrences` | Open occurrences | `records.view` |
| `battery_packs` | Battery packs and their retirement horizons | `aircraft.view` |
| `readiness` | The organization's readiness meter (record coverage percentages) and the setup steps still open | none needed |
| `maintenance_experience` | Repair verification and component survival, measured from your records | `maintenance.view` |

Organization admins' keys reach every tool. No tool returns member lists, email addresses or pilot identities.

Every figure is advisory and comes from the organization's own records. A readiness reading says what the records show; it never authorizes or clears a flight, and an assistant's answer built on it is no more than that.

## Protocol details

- Transport: Streamable HTTP, one JSON response per POST. Protocol revisions `2025-06-18`, `2025-03-26` and `2024-11-05`. No event stream and no sessions, so `GET` and `DELETE` answer `405` with `Allow: POST`.
- Methods: `initialize`, `ping`, `tools/list`, `tools/call`.
- Times are ISO 8601 with your organization's UTC offset; a date alone is a calendar day.
- Paging: send `recent_flights`' `next_cursor` back as `cursor`.

## Errors and limits

| Answer | Meaning |
|---|---|
| HTTP 401, JSON-RPC `-32001` | Missing or invalid key |
| HTTP 403, JSON-RPC `-32001` | The key lacks the MCP area, or its holder still owes two-factor or single sign-on |
| JSON-RPC `-32602` | A missing or unreadable argument, or an unknown tool; `error.data` names what is accepted |
| JSON-RPC `-32700` / `-32600` | A body that is not JSON / not a JSON-RPC request |
| HTTP 429, JSON-RPC `-32029` | Over the limit; `Retry-After` gives the seconds to wait |

MCP calls spend no API quota or credits. Each key may send 60 requests a minute and 1,000 an hour.

## Try it by hand

`mcp_call.py` is a standard-library client for checking a key before you hand it to an assistant:

```bash
export ROTORLAB_API_KEY="rl_your_key"
python mcp_call.py list
python mcp_call.py call recent_flights --args '{"limit": 5}'
python mcp_call.py call aircraft_health --args '{"aircraft": "Survey 1"}'
```

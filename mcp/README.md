# Connect an AI assistant (MCP)

RotorLab serves a read-only [Model Context Protocol](https://modelcontextprotocol.io) endpoint on the same address as the API:

    POST https://app.rotorlab.app/mcp

Point any MCP client that speaks Streamable HTTP (Claude, or your own agent) at it with an API key, and it can ask questions of your organization's records. RotorLab ships no model of its own: the assistant is yours, reading through your key.

## The key

1. In RotorLab, open Organization, Integrations, API keys.
2. Untick every area except **AI assistant (MCP) reads**, keep **Read only**, and choose the shortest end date that suits you. The endpoint never writes, and a key with only this area cannot call the rest of the API. A read-only key is enough: the endpoint never writes.
3. Copy the key when it is shown. It is shown once.

Send it as `Authorization: Bearer <key>`. The key's organization is the boundary for every read. A member's key sees only the tools their role reads, and two-factor and single sign-on rules apply to the key as they do to signing in.

## Claude Code

Set the key in your environment without typing it into a command, so it stays out of your shell history:

```bash
read -rs ROTORLAB_API_KEY && export ROTORLAB_API_KEY      # macOS, Linux or Git Bash; paste, then Enter
```

```powershell
$env:ROTORLAB_API_KEY = Read-Host "Paste your API key"   # Windows PowerShell
```

Then add the server in a project's `.mcp.json`. It reads the key from your environment, so the key is never written into the file, and this is the form that is safe to commit:

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

You can also add it from the command line:

```bash
claude mcp add --transport http rotorlab https://app.rotorlab.app/mcp \
  --header "Authorization: Bearer $ROTORLAB_API_KEY"
```

The shell expands the key before Claude Code sees it, so this command stores the key itself, in clear, in your user configuration (`~/.claude.json`). Keep the default local scope, and never run it with `--scope project`, which would write the key into a `.mcp.json` that gets committed. Prefer the `.mcp.json` form above.

Other clients take the same three facts: the URL, the HTTP (Streamable HTTP) transport, and the `Authorization` header.

## Tools

Every tool is a read, with an input schema, an output schema and read-only annotations, so a client can run them without asking. Each result carries `structuredContent` and the same JSON as text.

| Tool | What it reads | Role area a member's key needs |
|---|---|---|
| `fleet_overview` | The aircraft register with each aircraft's readiness reading; the names other tools take | Aircraft & registry (view) |
| `aircraft_health` | One aircraft's health flags and measured trends (argument: `aircraft`, a name, registration or serial) | Fleet health (view) |
| `recent_flights` | Recent flights, 20 a page by default and at most 50 (`limit`, `cursor`) | Flights & logs (view) |
| `open_work_orders` | Open work orders | Maintenance (view) |
| `open_occurrences` | Open occurrences | Safety records (view) |
| `battery_packs` | Battery packs and their retirement horizons | Aircraft & registry (view) |
| `readiness` | The organization's readiness meter (record coverage percentages) and the setup steps still open | every member |
| `maintenance_experience` | Repair verification and component survival, measured from your records | Maintenance (view) |

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
read -rs ROTORLAB_API_KEY && export ROTORLAB_API_KEY      # paste the key, then Enter
python mcp_call.py list
python mcp_call.py call recent_flights --args '{"limit": 5}'
python mcp_call.py call aircraft_health --args '{"aircraft": "<aircraft name>"}'
```

`mcp_call.py` sends the key only over `https://` (plain `http://` only to a server on your own machine) and never follows a redirect.

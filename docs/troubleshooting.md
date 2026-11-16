# Troubleshooting

The messages below are what the examples print, word for word. The Python scripts exit with status `2` for a setup problem, `1` when RotorLab refused the call, and `3` when RotorLab could not be reached.

## Before the first call

| Message | What it means and what to do |
|---|---|
| `Set ROTORLAB_API_KEY to your API key first. Create one in RotorLab under Organization, Integrations, API keys.` | No key in the environment. Set it as shown in the README, in the same terminal you run the script from. |
| `ROTORLAB_URL must start with https:// (plain http is allowed only for localhost): the key would cross the network in clear.` | `ROTORLAB_URL` uses `http://` for a host that is not this computer. Use `https://app.rotorlab.app`, or leave the variable unset. |
| `Set ROTORLAB_API_KEY to an API key that includes the 'AI assistant (MCP) reads' area.` | `mcp/mcp_call.py` found no key. Create one with only that area ticked. |
| `Set ROTORLAB_WEBHOOK_SECRET to the secret RotorLab showed when you added the webhook.` | `webhooks/receiver.py` needs the hook's secret. If you lost it, delete the hook and add it again to get a new one. |

## RotorLab refused the call

A refusal prints `RotorLab answered <status>: <sentence>`, followed by any field a program can branch on. The sentence says what to do.

| Status | Usual cause | What to do |
|---|---|---|
| `401` | The key is wrong, revoked or has ended, or its holder's access ended | Check the key was copied whole; create a new one if it was revoked or ended |
| `402` (`quota: "none"`) | The account lacks the add-on, or the plan has no API calls and no credits | Talk to your organization's administrator |
| `403` (`area`) | The key does not have the area this call needs | Create a key with that area ticked; see the Areas table in the README |
| `403` (`read_only`) | A read-only key tried to change a record | Use a read-and-write key for `file_flight.py` and `attach_log.py` |
| `403` (`mfa_setup_required`, `sso`) | The key's holder still owes two-factor or single sign-on | Sign in to RotorLab once and finish the setup |
| `404` | No such record in your organization, or a path that is not an endpoint | Check the id or name; records outside your organization answer `404` |
| `409` (`duplicate_of`) | The log is already stored with another flight | Nothing to do: the flight already has its log |
| `413` | The body is over the limit (4 MB JSON, 64 MB forensics log, 512 MB flight log) | Send a smaller file |
| `429` (`Retry-After`) | Today's quota and credits are spent, or five of your logs are waiting to be read | Wait the seconds in `Retry-After`; records calls are never metered |
| `503` (`token`, `status_url`) | A forensics log was not read in time | Collect it later from `status_url` at no further cost |

The full list is in the README under Errors and on https://rotorlab.app/developers.

## The network

| Message | What it means and what to do |
|---|---|
| `Could not reach RotorLab: ...` | No connection to the address in `ROTORLAB_URL`. Check the address, your connection, and any firewall. The wording after the colon comes from your system, for example `[WinError 10061] No connection could be made because the target machine actively refused it` on Windows. |
| `RotorLab answered 301` (or `302`, `307`, `308`) with a `Location` line | The address redirected. The scripts never follow a redirect, because it would carry your key to another address. Set `ROTORLAB_URL` to the address in `Location` if you trust it, usually `https://app.rotorlab.app`. |
| `Could not reach RotorLab: [SSL: CERTIFICATE_VERIFY_FAILED] ...` | Python could not verify the server's certificate. Update your system's certificate store (on macOS with the python.org installer, run its `Install Certificates.command`). The scripts never turn certificate checks off. |

## Webhook receiver answers

`receiver.py` answers each delivery with a short sentence. RotorLab retries anything that is not a `2xx`.

| Answer | Meaning |
|---|---|
| `200 ok` | Verified and handled |
| `200 already handled` | The same signed body was handled before; it was not acted on again |
| `200 too old, ignored` | A correctly signed delivery whose `at` is older than the replay window (24 hours) |
| `401 bad signature` | The signature does not match. Check that the secret is the one RotorLab showed for this hook, and that nothing between RotorLab and the receiver changes the body |
| `400 not JSON`, `400 not a RotorLab event` | The body is not a RotorLab event |
| `413 body too large` | The body is over the receiver's 1 MB limit |
| `500 not handled, retry` | Your `handle_event` raised. RotorLab tries again later with the same body |

A hook whose deliveries fail 20 times in a row is turned off, and an organization admin sees that on the Webhooks card. Fix the endpoint first.

## MCP

| Message | What it means and what to do |
|---|---|
| `HTTP 401, JSON-RPC -32001: ...` | Missing or invalid key |
| `HTTP 403, JSON-RPC -32001: ...` | The key lacks the MCP area, or its holder still owes two-factor or single sign-on |
| `HTTP <status>, JSON-RPC -32602: ...` | A missing or unreadable argument, or an unknown tool. The `data:` line names what is accepted |
| `HTTP 429, JSON-RPC -32029: ...` | Over 60 requests a minute or 1,000 an hour for this key. Wait the seconds in `Retry-After` |

## Still stuck

Open an issue with the question or bug template, with keys and secrets removed. For anything that looks like a security problem, write to security@rotorlab.app instead.

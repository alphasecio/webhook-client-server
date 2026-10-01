# webhook-client-server

A minimal webhook client-server demo built with Node.js/Express (server) and Streamlit (client), deployable as a two-service Railway template.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/WJuLbj?referralCode=alphasec)

---

## What It Does

The **server** receives HTTP POST requests on a parameterised route (`/webhook/:event`), optionally verifies an HMAC-SHA256 signature over the raw request body, logs the event, and returns the received data as JSON.

![Webhook server](/server/webhook-server.png)

The **client** is a Streamlit UI for sending webhook requests. You set a URL, event type, JSON payload and optional shared secret. If you provide a secret, the client signs the payload before sending it.

![Webhook client](/client/webhook-client.png)

Together they demonstrate the core webhook pattern: the sender signs the exact bytes it sends, the receiver recomputes the signature over the exact bytes it receives, and the shared secret itself never travels over the wire.

---

## Project Structure

```
webhook-client-server/
├── server/
│   ├── server.js         # Express webhook server
│   ├── package.json
│   └── railway.toml      # Railway deploy config for server service
└── client/
    ├── app.py            # Streamlit webhook client
    ├── requirements.txt
    ├── .python-version
    └── railway.toml      # Railway deploy config for client service
```

---

## Server

Built with Node.js and Express. Exposes the following endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Server info and available endpoints |
| `GET` | `/health` | Health check, returns `{ "status": "ok" }` |
| `POST` | `/webhook/:event` | Receives a webhook for any event name |

The event name comes from the `X-Event-Type` header if present, otherwise from the URL. JSON bodies (`application/json` or `application/*+json`) are parsed and echoed back. Any other content type is echoed back as text. Bodies are limited to 100 KB.

### Signature Verification

If `WEBHOOK_SECRET` is set, every request must carry an HMAC-SHA256 signature of the raw request body, hex-encoded:

```
X-Webhook-Signature: sha256=<hex_digest>
```

Requests with a missing or invalid signature return `401 Unauthorized`. If `WEBHOOK_SECRET` is not set, verification is skipped, all requests are accepted, and the server logs a warning at startup.

The signature is computed over the bytes as sent, not over a re-serialized copy of the JSON. Re-serializing changes whitespace and key formatting, which is the most common reason webhook signatures fail to match.

To send a signed request without the client:

```bash
SECRET=mysecret
BODY='{"id":1,"name":"Alice"}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')

curl -X POST http://localhost:3000/webhook/user.created \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=$SIG" \
  -d "$BODY"
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | No (default `3000`) | Port the server listens on |
| `WEBHOOK_SECRET` | Optional | Shared secret for HMAC-SHA256 signature verification |

---

## Client

Built with Streamlit. Provides a UI with the following fields:

- **Webhook URL**: defaults to the server's Railway private network address, so it works with no setup when deployed alongside the server
- **Event Type**: sent as the `X-Event-Type` header
- **Webhook Secret**: if provided, the payload is signed and sent as `X-Webhook-Signature: sha256=<digest>`
- **JSON Payload**: validated before sending, with a clear error on invalid JSON

The payload is sent as compact JSON (no extra whitespace), the same format JavaScript's `JSON.stringify` produces, and the signature covers exactly those bytes.

After you submit, the request headers, payload and server response are shown inline. Redirects are not followed, and response bodies are shown up to 1 MB.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | Auto-set by Railway | Port Streamlit listens on |
| `WEBHOOK_URL` | Optional | Default value for the Webhook URL field (default: `http://webhook-server.railway.internal:3000/webhook/test`) |

---

## Running Locally

**Server:**
```bash
cd server
npm install
WEBHOOK_SECRET=mysecret node server.js
```

**Client:**
```bash
cd client
pip install -r requirements.txt
streamlit run app.py
```

Then open the client at `http://localhost:8501`, change the Webhook URL to `http://localhost:3000/webhook/test`, set the secret to `mysecret`, and send a request.

---

## Deploying on Railway

The Railway template deploys both services automatically. The client's default Webhook URL points to `webhook-server.railway.internal:3000`, the server's address on Railway's private network, so it works without copying URLs. If you change the server's `PORT`, update the client's `WEBHOOK_URL` to match.

To enable signature verification after deployment, set `WEBHOOK_SECRET` on the server service and enter the same value in the client's Secret field.

---

## Security Notes

- **No replay protection.** The signature doesn't include a timestamp, so a captured signed request can be resent and will still verify. Production webhook schemes such as GitHub, Stripe and [Standard Webhooks](https://www.standardwebhooks.com/) sign a timestamp along with the body and reject old requests.
- **The client sends requests anywhere.** Anyone who can open the client can use it to POST to any URL from your Railway service. Remove the client's public domain, or put it behind authentication, if you leave it running.
- **Without `WEBHOOK_SECRET`, the server accepts anything.** That's useful for testing, but set a secret for any deployment you keep.

---

## Further Reading

- [Getting Started with Webhooks: Part 1 — Webhook Servers](https://alphasec.io/getting-started-with-webhooks-part-1-webhook-servers/)
- [Getting Started with Webhooks: Part 2 — Webhook Clients](https://alphasec.io/getting-started-with-webhooks-part-2-webhook-clients/)

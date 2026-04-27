# webhook-client-server

A minimal webhook client-server demo built with Node.js/Express (server) and Streamlit (client), deployable as a two-service Railway template.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/WJuLbj?referralCode=alphasec)

---

## What It Does

The **server** receives HTTP POST requests on a parameterised route (`/webhook/:event`), optionally verifies an HMAC-SHA256 signature, logs the event type and payload, and returns the received data as JSON.

![Webhook server](/server/webhook-server.png)

The **client** is a Streamlit UI for sending webhook requests — specify a URL, event type, JSON payload, and optional shared secret. If a secret is provided, the payload is signed automatically before sending.

![Webhook client](/client/webhook-client.png)

Together they demonstrate the core webhook pattern: a sender signs a payload, a receiver verifies the signature, and both sides use a shared secret without transmitting it directly.

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
    └── railway.toml      # Railway deploy config for client service
```

---

## Server

Built with Node.js and Express. Exposes the following endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Server info and available endpoints |
| `GET` | `/health` | Health check — returns `{ "status": "ok" }` |
| `POST` | `/webhook/:event` | Receives webhook for any event name |

### Signature Verification

If `WEBHOOK_SECRET` is set as an environment variable, the server verifies the `X-Webhook-Signature` header using HMAC-SHA256:

```
X-Webhook-Signature: sha256=<hex_digest>
```

Requests with a missing or invalid signature return `401 Unauthorized`. If `WEBHOOK_SECRET` is not set, signature verification is skipped and all requests are accepted.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | Auto-set by Railway | Port the server listens on |
| `WEBHOOK_SECRET` | Optional | Shared secret for HMAC-SHA256 signature verification |

---

## Client

Built with Streamlit. Provides a UI with the following fields:

- **Webhook URL** — defaults to the Railway internal hostname for zero-config use when deployed alongside the server
- **Event Type** — sent as `X-Event-Type` header
- **Webhook Secret** — if provided, signs the payload as `X-Webhook-Signature: sha256=<digest>`
- **JSON Payload** — validated before sending; displays a clear error on invalid JSON

The request/response are displayed inline after submission, including the headers sent and the full server response.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | Auto-set by Railway | Port Streamlit listens on |

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

The Railway template deploys both services automatically. The client's default Webhook URL points to `webhook-server.railway.internal` — Railway's private network hostname for the server service — so it works out of the box without copying URLs.

To enable signature verification after deployment, set `WEBHOOK_SECRET` on the server service and enter the same value in the client's Secret field.

---

## Further Reading

- [Getting Started with Webhooks: Part 1 — Webhook Servers](https://alphasec.io/getting-started-with-webhooks-part-1-webhook-servers/)
- [Getting Started with Webhooks: Part 2 — Webhook Clients](https://alphasec.io/getting-started-with-webhooks-part-2-webhook-clients/)

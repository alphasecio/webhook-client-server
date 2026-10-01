"use strict";

const crypto = require("node:crypto");
const express = require("express");

const port = Number(process.env.PORT) || 3000;
const secret = (process.env.WEBHOOK_SECRET || "").trim();
const SIGNATURE_PATTERN = /^sha256=([0-9a-f]{64})$/i;
const JSON_TYPE = /^application\/(?:[\w.+-]+\+)?json\b/i;

const app = express();
app.disable("x-powered-by");

// HMAC-SHA256 over the exact bytes received, compared in constant time.
function isValidSignature(header, rawBody) {
  const match = typeof header === "string" && SIGNATURE_PATTERN.exec(header.trim());
  if (!match) return false;
  const expected = crypto.createHmac("sha256", secret).update(rawBody).digest();
  return crypto.timingSafeEqual(Buffer.from(match[1], "hex"), expected);
}

function parseBody(req, rawBody) {
  if (rawBody.length === 0) return null;
  const text = rawBody.toString("utf8");
  return JSON_TYPE.test(req.get("content-type") || "") ? JSON.parse(text) : text;
}

app.get("/", (req, res) => {
  res.json({ message: "Webhook server is running.", endpoints: ["/health", "/webhook/:event"] });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.post(
  "/webhook/:event",
  express.raw({ type: () => true, limit: "100kb" }),
  (req, res) => {
    const eventType = req.get("x-event-type") || req.params.event;
    const rawBody = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);
    const timestamp = new Date().toISOString();

    if (secret && !isValidSignature(req.get("x-webhook-signature"), rawBody)) {
      console.warn(`[${timestamp}] Invalid signature for event ${JSON.stringify(eventType)}`);
      return res.status(401).json({ error: "Invalid signature." });
    }

    let data;
    try {
      data = parseBody(req, rawBody);
    } catch {
      return res.status(400).json({ error: "Invalid JSON body." });
    }

    console.log(`[${timestamp}] Webhook received`);
    console.log("Event:", JSON.stringify(eventType));
    console.log("Headers:", {
      "content-type": req.get("content-type"),
      "user-agent": req.get("user-agent"),
      "x-event-type": req.get("x-event-type"),
      "x-webhook-signature": req.get("x-webhook-signature") ? "present" : "absent",
    });
    console.log("Body:", JSON.stringify(data, null, 2));

    res.json({
      message: "Webhook received successfully.",
      event: eventType,
      receivedData: data,
    });
  }
);

app.use((req, res) => {
  res.status(404).json({ error: "Not Found" });
});

// Error handler (must be registered last). Body-parser errors carry a 4xx status.
app.use((err, req, res, next) => {
  const status = Number(err.status || err.statusCode) || 500;
  if (status >= 500) {
    console.error("Error:", err.stack);
    return res.status(500).json({ error: "Internal Server Error" });
  }
  res.status(status).json({ error: err.expose ? err.message : "Bad Request" });
});

const server = app.listen(port, (err) => {
  if (err) throw err;
  console.log(`Webhook server listening on port ${port}`);
  if (!secret) {
    console.warn("WEBHOOK_SECRET is not set: signature verification is disabled and all requests are accepted.");
  }
});

process.on("SIGTERM", () => server.close(() => process.exit(0)));

const express = require("express");
const cors = require("cors");
const crypto = require("crypto");
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// HMAC-SHA256 signature verification
function verifySignature(req, secret) {
  const signature = req.headers["x-webhook-signature"];
  if (!signature) return false;
  const expected = `sha256=${crypto
    .createHmac("sha256", secret)
    .update(JSON.stringify(req.body))
    .digest("hex")}`;
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected)
    );
  } catch {
    return false;
  }
}

// Routes
app.get("/", (req, res) => {
  res.json({ message: "Webhook server is running.", endpoints: ["/health", "/webhook/:event"] });
});
 
app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});
 
app.post("/webhook/:event", (req, res) => {
  const { event } = req.params;
  const eventType = req.headers["x-event-type"] || event;
 
  // Verify signature if WEBHOOK_SECRET is set
  if (process.env.WEBHOOK_SECRET) {
    if (!verifySignature(req, process.env.WEBHOOK_SECRET)) {
      console.warn(`[${new Date().toISOString()}] Invalid signature for event: ${eventType}`);
      return res.status(401).json({ error: "Invalid signature." });
    }
  }
 
  console.log(`[${new Date().toISOString()}] Webhook received`);
  console.log("Event:", eventType);
  console.log("Headers:", req.headers);
  console.log("Body:", JSON.stringify(req.body, null, 2));
 
  res.json({
    message: `Webhook received successfully.`,
    event: eventType,
    receivedData: req.body,
  });
});
 
// Error handler (must be registered after routes)
app.use((err, req, res, next) => {
  console.error("Error:", err.stack);
  res.status(500).json({ error: "Internal Server Error" });
});
 
app.listen(port, () => {
  console.log(`Webhook server running at http://localhost:${port}/`);
});
